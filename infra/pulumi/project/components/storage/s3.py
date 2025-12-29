# components/storage/s3.py
from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

RAW_DATA_BUCKET_NAME: Final[str] = "stock-market-raw-data-1996"
ATHENA_RESULTS_BUCKET_NAME: Final[str] = "stock-market-athena-results-1996"


# ============================================================
# Factory functions
# ============================================================

def create_raw_data_bucket() -> aws.s3.Bucket:
    """
    Creates the S3 bucket used to store raw stock market data.
    """

    bucket: aws.s3.Bucket = aws.s3.Bucket(
        resource_name="rawStockDataBucket",
        bucket=RAW_DATA_BUCKET_NAME,
        acl="private",
        tags={
            "Project": "StockMarketRealTimePipeline",
            "Purpose": "RawStockData",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    aws.s3.BucketPublicAccessBlock(
        resource_name="rawStockDataPublicAccessBlock",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    return bucket


def create_athena_results_bucket() -> aws.s3.Bucket:
    """
    Creates the S3 bucket used to store Athena query results.
    """

    bucket: aws.s3.Bucket = aws.s3.Bucket(
        resource_name="athenaResultsBucket",
        bucket=ATHENA_RESULTS_BUCKET_NAME,
        acl="private",
        tags={
            "Project": "StockMarketRealTimePipeline",
            "Purpose": "AthenaQueryResults",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    aws.s3.BucketPublicAccessBlock(
        resource_name="athenaResultsPublicAccessBlock",
        bucket=bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    return bucket
