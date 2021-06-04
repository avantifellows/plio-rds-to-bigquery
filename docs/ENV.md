## Environment variables

This guide explains all the available configurations for your AWS Lambda environment. To configure Environment variables for your Lambda function, switch to the "Configuration" tab and then "Environment variables".

### Google & BigQuery settings
#### `BIGQUERY_PROJECT_ID`
The project id for your bigquery project. Generally, it's the name of your project.

#### `BIGQUERY_DATASET_ID`
The name of your dataset. You can check this by right-clicking on your dataset and click on "Open" option. It will show you a section with dataset info.
**Note:** Do NOT use fully qualified name like `project-id:dataset-id`. Only the part after colon is needed.

#### `BIGQUERY_REGION`
The region of your bigquery setup in Google Cloud Console. You can check this from the dataset info section mentioned above. You can find all supported regions [here](https://cloud.google.com/bigquery/docs/locations#regional-locations)

#### GOOGLE_APPLICATION_CREDENTIALS
The name of the JSON file that contains the service account credentials. To create a new service account when setting up the project, visit our [Installation guide](./INSTALLATION.md). The service account must have BigQuery admin permissions.
Based on your file name, here's what your value can look like: `gcp-service-account-filename.json`

### AWS RDS settings
The lambda function connects with RDS database to capture the schema definition and uses it when creating tables in BigQuery. Below are the environment variables you need to configure to connect to RDS:

#### `DB_HOST`
The database host. This is the RDS endpoint.

#### `DB_NAME`
Name of the database you want to query.

#### `DB_PORT`
Port for the database connection. Defaults to `5432`.

#### `DB_USER`
The name of the database user.

#### `DB_PASSWORD`
The password for the database user.

#### `DB_SCHEMA_NAME`
Name of the database schema that you want to query.

### AWS S3 settings
#### `S3_BUCKET_NAME`
The bucket name where you want to store the CSV data files. The bucket must be created before setting this value.

### `S3_DIRECTORY`
The directory inside the bucket where the CSV files should be stored. Defaults to empty string, i.e., within the main directory inside bucket.
