from __future__ import annotations

import base64
import json
import os
from decimal import Decimal
from typing import Any, Dict

import boto3


# =========================
# Environment variables
# =========================

DYNAMO_TABLE: str = os.environ["DYNAMO_TABLE"]
RAW_BUCKET: str = os.environ["RAW_BUCKET"]


# =========================
# AWS clients
# =========================

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

table = dynamodb.Table(DYNAMO_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    for record in event["Records"]:
        try:
            payload = json.loads(
                base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            )

            # Save raw data to S3
            s3.put_object(
                Bucket=RAW_BUCKET,
                Key=f"raw-data/{payload['symbol']}/{payload['timestamp'].replace(':', '-')}.json",
                Body=json.dumps(payload),
                ContentType="application/json",
            )

            # Compute metrics
            price_change = payload["price"] - payload["previous_close"]
            moving_average = (
                payload["open"]
                + payload["high"]
                + payload["low"]
                + payload["price"]
            ) / 4

            # Store processed data in DynamoDB
            table.put_item(
                Item={
                    "symbol": payload["symbol"],
                    "timestamp": payload["timestamp"],
                    "price": Decimal(str(payload["price"])),
                    "previous_close": Decimal(str(payload["previous_close"])),
                    "change": Decimal(str(price_change)),
                    "moving_average": Decimal(str(moving_average)),
                }
            )

        except Exception as exc:
            print(f"Error processing record: {exc}")

    return {"statusCode": 200}
