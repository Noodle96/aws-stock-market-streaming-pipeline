# components/analytics/glue.py
from __future__ import annotations

from typing import Final

import pulumi
import pulumi_aws as aws

# ============================================================
# Constants
# ============================================================

GLUE_DATABASE_NAME: Final[str] = "stock_data_db"

# ============================================================
# Glue Database
# ============================================================

def create_glue_database() -> aws.glue.CatalogDatabase:
    """
    Creates a Glue Data Catalog database for stock market raw data.
    """

    glue_database: aws.glue.CatalogDatabase = aws.glue.CatalogDatabase(
        resource_name="stockDataGlueDatabase",
        name=GLUE_DATABASE_NAME,
        description="Glue database for raw stock market data stored in S3",
    )

    pulumi.export("glue_database_name", glue_database.name)

    return glue_database


def create_glue_table(
    *,
    database_name: pulumi.Input[str],
    raw_data_bucket_name: pulumi.Input[str],
) -> aws.glue.CatalogTable:
    """
    Creates a Glue table over JSON files stored in S3.
    """

    table: aws.glue.CatalogTable = aws.glue.CatalogTable(
        resource_name="stockDataGlueTable",
        database_name=database_name,
        name="stock_data_table",
        table_type="EXTERNAL_TABLE",
        parameters={
            "classification": "json",
        },
        storage_descriptor=aws.glue.CatalogTableStorageDescriptorArgs(
            location=raw_data_bucket_name.apply(
                lambda b: f"s3://{b}/raw-data/"
            ),
            input_format="org.apache.hadoop.mapred.TextInputFormat",
            output_format="org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat",
            # serde_info=aws.glue.CatalogTableStorageDescriptorSerdeInfo(
            #     serialization_library="org.openx.data.jsonserde.JsonSerDe",
            # ),
            ser_de_info={
                "serializationLibrary": "org.openx.data.jsonserde.JsonSerDe",
                "parameters": {
                    "ignore.malformed.json": "true"
                },
            },
            columns=[
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="symbol", type="string"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="timestamp", type="string"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="open", type="double"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="high", type="double"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="low", type="double"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="price", type="double"
                ),
                aws.glue.CatalogTableStorageDescriptorColumnArgs(
                    name="previous_close", type="double"
                ),
                    aws.glue.CatalogTableStorageDescriptorColumnArgs(
                        name="volume", type="int"
                ),
            ],
        ),
    )

    pulumi.export("glue_table_name", table.name)

    return table
