from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws


def create_kinesis_processor_lambda(
    kinesis_stream_arn: pulumi.Input[str],
    dynamo_table_name: pulumi.Input[str],
    raw_bucket_name: pulumi.Input[str],
    role_arn: pulumi.Input[str],
) -> aws.lambda_.Function:

    return aws.lambda_.Function(
        resource_name="kinesisProcessorLambda",
        name="kinesis-processor",
        runtime="python3.10",
        handler="handler.lambda_handler",
        role=role_arn,
        timeout=30,
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables={
                "DYNAMO_TABLE": dynamo_table_name,
                "RAW_BUCKET": raw_bucket_name,
            }
        ),
        code=pulumi.AssetArchive(
            {
                ".": pulumi.FileArchive(
                    "../project/lambdas/kinesis_processor"
                )
            }
        ),
    )



def create_kinesis_event_source_mapping(
    *,
    kinesis_stream_arn: pulumi.Input[str],
    lambda_function_name: pulumi.Input[str],
) -> aws.lambda_.EventSourceMapping:
    """
    Connects a Kinesis Data Stream to a Lambda function.
    """

    event_source_mapping: aws.lambda_.EventSourceMapping = aws.lambda_.EventSourceMapping(
        resource_name="kinesisToLambdaMapping",
        event_source_arn=kinesis_stream_arn,
        function_name=lambda_function_name,
        starting_position="LATEST",
        batch_size=2,
        enabled=True,
    )

    pulumi.export("kinesis_lambda_mapping_uuid", event_source_mapping.uuid)

    return event_source_mapping