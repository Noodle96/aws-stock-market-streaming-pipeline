# infra/pulumi/project/lambdas/trend_alert/app.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import boto3

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")


@dataclass(frozen=True)
class Config:
    table_name: str
    sns_topic_arn: str


def load_config() -> Config:
    """
    Loads required environment variables.
    Raises KeyError if missing (good: fail fast).
    """
    table_name: str = os.environ["TABLE_NAME"]
    sns_topic_arn: str = os.environ["SNS_TOPIC_ARN"]
    return Config(table_name=table_name, sns_topic_arn=sns_topic_arn)


def _to_decimal(value: Any) -> Decimal:
    """
    Ensures numeric values are treated as Decimal for DynamoDB safety.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def extract_new_image(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    DynamoDB Streams record -> get the NewImage dict, if present.
    """
    ddb: Dict[str, Any] = record.get("dynamodb", {})
    new_image: Optional[Dict[str, Any]] = ddb.get("NewImage")
    return new_image


def parse_ddb_number(field: Dict[str, str]) -> Decimal:
    """
    DynamoDB streams encodes numbers like {"N": "123.45"}.
    """
    return Decimal(field["N"])


def parse_ddb_string(field: Dict[str, str]) -> str:
    """
    DynamoDB streams encodes strings like {"S": "text"}.
    """
    return field["S"]


def compute_change_percent(price: Decimal, previous_close: Decimal) -> Decimal:
    if previous_close == 0:
        return Decimal("0")
    return (price - previous_close) / previous_close * Decimal("100")


def publish_alert(topic_arn: str, subject: str, message: str) -> None:
    sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message,
    )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print("In lambda handler")
    """
    Trigger: DynamoDB Stream (NEW_IMAGE)
    Action: Send SNS alert on anomalous movement.
    """
    cfg: Config = load_config()

    records: List[Dict[str, Any]] = event.get("Records", [])
    table = dynamodb.Table(cfg.table_name)

    alerts_sent: int = 0
    for rec in records:
        print(f"\t[LAMBDA HANDLER]rec: {rec}")
        new_image = extract_new_image(rec)
        if new_image is None:
            continue

        # Expect these fields from your processed DynamoDB item
        symbol: str = parse_ddb_string(new_image["symbol"])
        timestamp: str = parse_ddb_string(new_image["timestamp"])

        price: Decimal = parse_ddb_number(new_image["price"])
        prev_close: Decimal = parse_ddb_number(new_image["previous_close"])

        change_percent: Decimal = compute_change_percent(price, prev_close)

        # Simple anomaly rule (same spirit as before)
        threshold: Decimal = Decimal("0.2050")
        print("\t[LAMBDA HANDLER] In lambda handler: threshold =", threshold)
        print("\t[LAMBDA HANDLER] In lambda handler: change_percent =", change_percent)
        if abs(change_percent) > threshold:
            subject: str = f"Stock Alert: {symbol}"
            message: str = (
                f"ALERTA: movimiento anómalo detectado\n"
                f"symbol: {symbol}\n"
                f"timestamp: {timestamp}\n"
                f"price: {price}\n"
                f"previous_close: {prev_close}\n"
                f"change_percent: {change_percent:.2f}%\n"
            )
            publish_alert(cfg.sns_topic_arn, subject, message)
            alerts_sent += 1

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"records_received": len(records), "alerts_sent": alerts_sent}
        ),
    }
