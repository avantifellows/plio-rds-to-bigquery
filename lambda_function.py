# This file contains the main handler function that will be run by the AWS Lambda upon trigger.
# It copies data from an S3 folder and put them into a BigQuery dataset.

import boto3
import os
import psycopg2
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def lambda_handler(event, context):
    """The main handler function. """
    # load env variables
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID")
    bigquery_region = os.getenv("BIGQUERY_REGION")

    client = bigquery.Client(project=project_id, location=bigquery_region)

    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
    except NotFound:
        # create dataset if NotFound error
        client.create_dataset(dataset_id)

    # process tables in public schema
    table_names = get_tables_in_schema(public_mode=True)
    process_tables(client, dataset_ref, "public", table_names)

    # process tables in organization schema
    schema = os.getenv("DB_SCHEMA_NAME", None)
    table_names = get_tables_in_schema(public_mode=False)
    if schema is not None:
        process_tables(client, dataset_ref, schema, table_names)

    return {"statusCode": 200, "body": "All done!"}


def get_table_schema(table_name, schema):
    """Returns the schema for the specified database table as per BigQuery table schema format."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", 5432)

    # create connection
    con = psycopg2.connect(
        database=database, user=user, password=password, host=host, port=port
    )
    cur = con.cursor()

    # get the table column names and data types from postgres db
    cur.execute(
        f"select column_name, data_type from information_schema.columns where table_schema='{schema}' and table_name='{table_name}'"
    )
    rows = cur.fetchall()
    schema = []
    for row in rows:
        # row[0] is column name
        # row[1] is data type
        schema.append(bigquery.SchemaField(row[0], map_to_big_query_data_type(row[1])))

    return schema


def map_to_big_query_data_type(column_type):
    """Converts Postgres column types into BigQuery column types."""
    if (
        column_type.startswith("int")
        or column_type.startswith("bigint")
        or column_type.startswith("smallint")
    ):
        return "INT64"
    if column_type.startswith("bool"):
        return "BOOLEAN"
    if column_type.startswith("double") or column_type.startswith("decimal"):
        return "FLOAT64"
    if (
        column_type.startswith("char")
        or column_type.startswith("text")
        or column_type.startswith("json")
    ):
        return "STRING"
    if column_type.startswith("timestamp"):
        return "TIMESTAMP"
    if column_type.startswith("datetime"):
        return "DATETIME"
    if column_type.startswith("date"):
        return "DATE"
    if column_type.startswith("time"):
        return "TIME"


def get_tables_in_schema(public_mode=True):
    """
    List of organization tables that need to be processed.

    public_mode: Boolean field. If true, it returns tables that contain generic information from `public` schema. If false, it returns tenant specific tables from tenant schema.
    """
    if public_mode:
        return [
            "organization",
            "organization_user",
            "role",
            "user",
            "user_meta",
        ]

    return [
        "event",
        "experiment",
        "experiment_plio",
        "item",
        "model_has_tag",
        "plio",
        "question",
        "session",
        "session_answer",
        "tag",
        "video",
    ]


def process_tables(client, dataset_ref, schema, table_names):
    """Processes tables in the specified schema."""
    bucket_name = os.getenv("S3_BUCKET_NAME")
    s3_directory = os.getenv("S3_DIRECTORY", "")
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID")
    s3 = boto3.client("s3")

    for table_name in table_names:
        table_ref = dataset_ref.table(table_name)
        try:
            client.get_table(table_ref)
        except NotFound:
            # create table if NotFound error
            table_id = f"{project_id}.{dataset_id}.{table_name}"
            table = bigquery.Table(table_id, get_table_schema(table_name, schema))
            client.create_table(table)

        # download s3 file into lambda /tmp/ directory to upload to BigQuery
        file = s3_directory + table_name + ".csv"
        local_file_name = "/tmp/" + table_name + ".csv"
        s3.download_file(bucket_name, file, local_file_name)

        # bigquery transfer job configurations
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.CSV
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        job_config.allow_quoted_newlines = True

        # load the csv into bigquery
        with open(local_file_name, "rb") as source_file:
            job = client.load_table_from_file(
                source_file, table_ref, job_config=job_config
            )

        job.result()  # Waits for table load to complete.

        # looks like everything worked :)
        print(
            "Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_name)
        )
