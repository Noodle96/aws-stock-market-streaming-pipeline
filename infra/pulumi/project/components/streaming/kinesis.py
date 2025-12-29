# components/streaming/kinesis.py
from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

STREAM_NAME: Final[str] = "stock-market-stream"
RETENTION_HOURS: Final[int] = 24


# ============================================================
# Factory function
# ============================================================

def create_stock_stream() -> aws.kinesis.Stream:
    """
    Creates the Kinesis Data Stream used to ingest real-time stock data.

    Returns
    -------
    aws.kinesis.Stream
        The created Kinesis stream resource.
    """

    stream: aws.kinesis.Stream = aws.kinesis.Stream(
        resource_name="stockMarketStream",
        name=STREAM_NAME,
        retention_period=RETENTION_HOURS,
        stream_mode_details=aws.kinesis.StreamStreamModeDetailsArgs(
            stream_mode="ON_DEMAND"
        ),
        tags={
            "Project": "StockMarketRealTimePipeline",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    return stream
