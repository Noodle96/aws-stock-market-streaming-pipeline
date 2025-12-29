# components/messaging/sns.py
from __future__ import annotations

from typing import Final, Optional

import pulumi
import pulumi_aws as aws

TOPIC_NAME: Final[str] = "Stock_Trend_Alerts"

def create_stock_trend_topic(
    topic_name: str = TOPIC_NAME,
    email_subscription: Optional[str] = None,
) -> aws.sns.Topic:
    """
    Create an SNS Topic for stock trend alerts.

    Optionally, you can attach an email subscription if email_subscription is provided.
    """
    topic: aws.sns.Topic = aws.sns.Topic(
        resource_name="stockTrendAlertsTopic",
        name=topic_name,
        tags={
            "Project": "StockMarketRealTimePipeline",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    # Optional subscription (email)
    if email_subscription is not None:
        aws.sns.TopicSubscription(
            resource_name="stockTrendAlertsEmailSubscription",
            topic=topic.arn,
            protocol="email",
            endpoint=email_subscription,
        )

    return topic
