## AWS Data Pipeline
Plio RDS to BigQuery uses AWS Data Pipeline to extract data from RDS and put it in an S3 bucket as CSV files.

A new Data Pipeline has to be created for every database schema, including `public`. A new Data Pipeline can be very easily created using the `data-pipeline-template.json`.

Here are the simple steps to set it up:
1. Make a copy of the `data-pipeline-template.json` file. It is located at the root folder of this project.
   1. Update the values at the bottom of the file for the RDS and S3.
   2. Make sure to update the value of `pipelineLogUri` that's defined somewhere inside the JSON. This should contain the URI for the S3 bucket where you want to store Data Pipeline Logs.
2. Use this file within the `Create new Data Pipeline` form by selecting the `Import a definition` option and then `Load local file`.

Here are all the configurations you need to modify within your copy of `data-pipeline-template.json` before uploading.

**Note:** All variables in Data Pipeline have to start with `my` prefix. Do not update any variable name, only update the corresponding values.

#### myEC2InstanceType
The type of EC2 instance where the data extraction queries and CSV generation will happen. Default is `t2.micro`. It should be sufficient for Plio setup, however, if you want to change it to a higher/lower configuration, please feel free.

#### myRDSInstanceId
The instance ID of the RDS. This can be retrieved from your `RDS dashboard > RDS list > RDS instance`.

#### myRDSDBName
The database name within the RDS instance. The data pipeline will extract the data within tables inside this database.

#### myRDSUsername
The RDS user for connection.

#### *myRDSPassword
The RDS user password.

#### myRDSRegion
The AWS region for the RDS instance.

#### myRDSSchema
The database schema within the database you want to query. Since every organization has a schema, every data pipeline set up requires this.

#### myOutputS3Loc
The location of the S3 bucket where CSV files need to be added. If you have multiple data-pipelines, you may want to put all their output within a single bucket, separated by organization folder. For example, a typical value for this variable can be like:
```
s3://bucket_name/my_organization/"
```


#### pipelineLogUri
This variable is not located in the values section due to template reader restrictions. This value must be defined somewhere inside the JSON file. Search for `pipelineLogUri` and update its value.
This variable should contain the location for S3 bucket where Data Pipeline logs need to be added. If you have multiple data-pipelines, you may want to put all their logs within a single bucket, separated by organization folder. For example, a typical value for this variable can be like:
```
s3://logs_bucket_name/my_organization/
```
