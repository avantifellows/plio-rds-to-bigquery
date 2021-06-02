import json
import boto3
import os
import psycopg2
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def lambda_handler(event, context):
    project_id = os.getenv("PROJECT_ID")
    dataset_id = os.getenv("DATASET_ID")
    bucket_name = os.getenv("BUCKET_NAME")
    s3_directory = os.getenv("S3_DIRECTORY")
    bigquery_region = os.getenv("BIGQUERY_REGION")
    s3 = boto3.client("s3")
    client = bigquery.Client(project=project_id, location=bigquery_region)

    try:
        dataset_ref = client.dataset(dataset_id)
        client.get_dataset(dataset_ref)
    except NotFound:
        client.create_dataset(dataset_id)

    table_names = get_tables_to_process()
    for table_name in table_names:
        try:
            table_ref = dataset_ref.table(table_name)
            table = client.get_table(table_ref)
        except NotFound:
            table_id = f"{project_id}.{dataset_id}.{table_name}"
            table = bigquery.Table(table_id, get_table_schema(table_name))
            table = client.create_table(table)

        file = s3_directory + table_name + ".csv"
        local_file_name = "/tmp/" + table_name + ".csv"
        s3.download_file(bucket_name, file, local_file_name)

        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.CSV
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

    return {"statusCode": 200, "body": "All done!"}


def get_table_schema(table_name):
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", 5432)
    schema = os.getenv("DB_SCHEMA_NAME")

    con = psycopg2.connect(
        database=database, user=user, password=password, host=host, port=port
    )
    cur = con.cursor()
    cur.execute(
        f"select column_name, data_type from information_schema.columns where table_schema='{schema}' and table_name='{table_name}'"
    )
    rows = cur.fetchall()
    schema = []
    for row in rows:
        schema.append(bigquery.SchemaField(row[0], map_to_big_query_data_type(row[1])))

    return schema


def map_to_big_query_data_type(column_type):
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


def get_tables_to_process():
    return [
        "plio",
        "item",
        "experiment",
        "question",
        "session",
        "user",
        "organization",
        "role",
    ]
