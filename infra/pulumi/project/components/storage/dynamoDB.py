# components/storage/dynamoDB.py
from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

TABLE_NAME: Final[str] = "stock-market-data"
PARTITION_KEY: Final[str] = "symbol"
SORT_KEY: Final[str] = "timestamp"


# ============================================================
# Factory function
# ============================================================

def create_stock_table() -> aws.dynamodb.Table:
    """
    Create DynamoDB table for processed stock data.

    - Partition key: symbol (S)
    - Sort key: timestamp (S)
    - Billing mode: PAY_PER_REQUEST (on-demand)
    - DynamoDB Streams enabled to trigger downstream Lambda.
    """

    table: aws.dynamodb.Table = aws.dynamodb.Table(
        resource_name="stockMarketDataTable",
        name=TABLE_NAME,
        billing_mode="PAY_PER_REQUEST",
        hash_key=PARTITION_KEY,
        range_key=SORT_KEY,
        attributes=[
            aws.dynamodb.TableAttributeArgs(name=PARTITION_KEY, type="S",),
            aws.dynamodb.TableAttributeArgs(name=SORT_KEY, type="S",),
        ],
        stream_enabled=True,
        stream_view_type="NEW_IMAGE",
        tags={
            "Project": "StockMarketRealTimePipeline",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    return table
