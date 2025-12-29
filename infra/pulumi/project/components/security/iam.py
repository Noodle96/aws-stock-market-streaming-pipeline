# components/security/iam.py
from __future__ import annotations

from typing import Final, List

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

LAMBDA_ROLE_NAME: Final[str] = "Lambda_Kinesis_DynamoDB_Role"

MANAGED_POLICY_ARNS: Final[List[str]] = [
    "arn:aws:iam::aws:policy/AmazonKinesisFullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonSNSFullAccess", # para SNS
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
]


# ============================================================
# Factory function
# ============================================================

def create_lambda_execution_role() -> aws.iam.Role:
    """
    Creates the IAM Role used by Lambda functions that consume
    Kinesis streams and write to DynamoDB and S3.
    """

    role: aws.iam.Role = aws.iam.Role(
        resource_name="lambdaExecutionRole",
        name=LAMBDA_ROLE_NAME,
        assume_role_policy=aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            type="Service",
                            identifiers=["lambda.amazonaws.com"],
                        )
                    ],
                    actions=["sts:AssumeRole"],
                )
            ]
        ).json,
        tags={
            "Project": "StockMarketRealTimePipeline",
            "ManagedBy": "Pulumi",
            "Environment": pulumi.get_stack(),
        },
    )

    for index, policy_arn in enumerate(MANAGED_POLICY_ARNS):
        aws.iam.RolePolicyAttachment(
            resource_name=f"lambdaPolicyAttachment-{index}",
            role=role.name,
            policy_arn=policy_arn,
        )

    return role
