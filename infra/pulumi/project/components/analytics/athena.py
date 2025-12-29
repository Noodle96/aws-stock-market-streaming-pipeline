from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

WORKGROUP_NAME: Final[str] = "stock-market-athena-wg"

# ============================================================
# Athena WorkGroup
# ============================================================

def create_athena_workgroup(
    results_bucket_name: pulumi.Input[str],
) -> aws.athena.Workgroup:
    """
    Creates an Athena WorkGroup with controlled output location.
    """

    workgroup: aws.athena.Workgroup = aws.athena.Workgroup(
        resource_name="stockMarketAthenaWorkgroup",
        name=WORKGROUP_NAME,
        state="ENABLED",
        configuration=aws.athena.WorkgroupConfigurationArgs(
            enforce_workgroup_configuration=True,
            result_configuration=aws.athena.WorkgroupConfigurationResultConfigurationArgs(
                output_location=results_bucket_name.apply(
                    lambda bucket: f"s3://{bucket}/athena-results/"
                )
            ),
        ),
        tags={
            "Project": "StockMarketRealTimePipeline",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    return workgroup
