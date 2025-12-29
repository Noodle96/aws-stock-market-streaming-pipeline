from __future__ import annotations

import pulumi
import pulumi_aws as aws

# =========================
# Streaming layer
# =========================
from components.streaming.kinesis import create_stock_stream

# =========================
# Security layer
# =========================
from components.security.iam import create_lambda_execution_role

# =========================
# Storage layer
# =========================
from components.storage.dynamoDB import create_stock_table
from components.storage.s3 import (
    create_raw_data_bucket,
    create_athena_results_bucket,
)

# =========================
# Compute layer
# =========================
from components.compute.lambda_kinesis_processor import (
    create_kinesis_processor_lambda,
    create_kinesis_event_source_mapping,
)
from components.compute.lambda_trend_alert import (
    create_trend_alert_lambda,
    create_dynamodb_stream_event_source_mapping,
    TrendAlertLambdaArgs,
)

# ============================================================
# Analytics layer
# ============================================================
from components.analytics.glue import (
    create_glue_database,
    create_glue_table,
)
from components.analytics.athena import create_athena_workgroup

# ============================================================
# Messaging layer
# ============================================================
from components.messaging.sns import create_stock_trend_topic






# ============================================================
# 1. Create Kinesis Data Stream
# ============================================================
stock_stream: aws.kinesis.Stream = create_stock_stream()

# ============================================================
# 2. Create IAM Role for Lambda
# ============================================================
lambda_execution_role: aws.iam.Role = create_lambda_execution_role()

# ============================================================
# 3. Create DynamoDB Table
# ============================================================
stock_table: aws.dynamodb.Table = create_stock_table()

# ============================================================
# 4. Create S3 Buckets
# ============================================================
raw_data_bucket: aws.s3.Bucket = create_raw_data_bucket()
athena_results_bucket: aws.s3.Bucket = create_athena_results_bucket()

# ============================================================
# 5. Create Lambda Function for Kinesis Processing
# ============================================================
kinesis_processor_lambda: aws.lambda_.Function = (
    create_kinesis_processor_lambda(
        kinesis_stream_arn=stock_stream.arn,
        dynamo_table_name=stock_table.name,
        raw_bucket_name=raw_data_bucket.bucket,
        role_arn=lambda_execution_role.arn,
    )
)

# ============================================================
# 6. Create Event Source Mapping from Kinesis to Lambda
# ============================================================
kinesis_lambda_mapping = create_kinesis_event_source_mapping(
    kinesis_stream_arn=stock_stream.arn,
    lambda_function_name=kinesis_processor_lambda.name,
)

# ============================================================
# 7. Create Glue Database and Table
# ============================================================

glue_database = create_glue_database()

glue_table = create_glue_table(
    database_name=glue_database.name,
    raw_data_bucket_name=raw_data_bucket.bucket,
)

# ============================================================
# 8. Create Athena WorkGroup
# ============================================================
athena_workgroup = create_athena_workgroup(
    results_bucket_name=athena_results_bucket.bucket,
)

# ============================================================
# 9. SNS Topic + Trend Lambda (DynamoDB Streams -> Lambda -> SNS)
# ============================================================
sns_topic: aws.sns.Topic = create_stock_trend_topic(
    topic_name="Stock_Trend_Alerts",
    email_subscription="jorgealfredo.jatc@gmail.com"
)

trend_lambda: aws.lambda_.Function = create_trend_alert_lambda(
    TrendAlertLambdaArgs(
        role_arn=lambda_execution_role.arn,
        table_name=stock_table.name,
        dynamodb_stream_arn=stock_table.stream_arn,
        sns_topic_arn=sns_topic.arn,
    )   
)

dynamo_to_trend_mapping: aws.lambda_.EventSourceMapping = create_dynamodb_stream_event_source_mapping(
    dynamodb_stream_arn=stock_table.stream_arn,
    lambda_function_arn=trend_lambda.arn,
)



# ============================================================
# Stack outputs (debug / visibility)
# ============================================================

pulumi.export("kinesis_stream_name", stock_stream.name)
pulumi.export("kinesis_stream_arn", stock_stream.arn)

pulumi.export("lambda_role_name", lambda_execution_role.name)
pulumi.export("lambda_role_arn", lambda_execution_role.arn)

pulumi.export("dynamodb_table_name", stock_table.name)
pulumi.export("dynamodb_table_arn", stock_table.arn)

pulumi.export("raw_data_bucket_name", raw_data_bucket.bucket)
pulumi.export("raw_data_bucket_arn", raw_data_bucket.arn)

pulumi.export("athena_results_bucket_name", athena_results_bucket.bucket)
pulumi.export("athena_results_bucket_arn", athena_results_bucket.arn)

pulumi.export("kinesis_processor_lambda_name", kinesis_processor_lambda.name)
pulumi.export("kinesis_processor_lambda_arn", kinesis_processor_lambda.arn)

pulumi.export("athena_workgroup", athena_workgroup.name)

pulumi.export("sns_topic_arn", sns_topic.arn)
pulumi.export("trend_lambda_name", trend_lambda.name)
pulumi.export("trend_lambda_arn", trend_lambda.arn)

# pulumi up
# pulumi destroy
# pulumi stack output
