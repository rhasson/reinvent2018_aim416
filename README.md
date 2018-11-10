# AIM416 Build and ETL pipeline to analyze customer data
## Introduction
In this workshop we will use AWS Glue ETL to enrich [Amazon Product Review dataset](https://registry.opendata.aws/amazon-reviews/).  To do that we will pass the product review text to [Amazon Comprehend](https://aws.amazon.com/comprehend/) to detect sentiment, extract entities and key phrases which will be added to the original review dataset.  We will then save the dataset to Amazon S3 in Apache Parquet format so it can be quiered with [Amazon Athena](https://aws.amazon.com/athena/) and visualized with [Amazon QuickSight](https://aws.amazon.com/quicksight/).

## Authorization and permissions
Before we can start we need to define the appropriate policies and permissions for the differnet services to use.  In this workshop I assume you are logged in as a root user or a user with enough privilages to be able to create IAM roles and assign policies.  If you don't have that level of permission, either ask the owner of your account to help or create a personal account where you have more permission.

### Create Glue service role
Open the __IAM console__, select __Roles__ and click on __Create Role__.  In the list of services select __Glue__ and click next.  Add the following managed policies:  __AmazonS3FullAccess__, __AWSGlueServiceRole__, __ComprehendFullAccess__, __CloudWatchLogsReadOnlyAccess__.
Click next and finish creating the role.  In the list of roles, select your new role.  Click the __Trust Relationships__ tab, click __Edit Trust Relationship__ and make sure your trust policy looks like the following:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "comprehend.amazonaws.com",
          "ec2.amazonaws.com",
          "glue.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Getting Started
Start by downloading __comprehend_api.py__ to your local computer.  Then open the AWS Console and navigate to the S3 console.  If you don't already have one, create a bucket with a unique name.  S3 uses a flat namespace which means bucket names must be unique across all S3 customers.  Inside the bukcet, create a subfolder and name it __deps__ and upload __comprehend_api.py__ into the deps folder.  The __comprehend_api.py__ file includes a few functions that allow us to take a row field from our dataset and pass it to the Comprehend API.  
For this function to work as a UDF (user defined function) in [Apache Spark](http://spark.apache.org/docs/2.2.1/api/python/pyspark.sql.html) which AWS Glue uses under the hood, we need to wrap our function in a special UDF function factory.  To simplify our code for reability and extensibility we broke out these functions into their own file.

## Crawling Source Dataset
The next thing we need to do is use AWS Glue crawler to discover and catalog our source dataset which will then create a schema for us in the AWS Glue Data Catalog.  Open the AWS Glue console and navigate to __Crawlers__ under the __Data Catalog__ section on the left side of the console.  Click on __Add Crawler__ and follow the wizard accepting all of the defaults.  When it asks you to specific an __Include Path__ select __specficied path in another account__ and enter __s3://amazon-reviews-pds/parquet/__ in the include path text box.  Next, when asked to __choose an IAM role__ select __create an IAM role__ and give it a name.  Note that does role will create IAM S3 policies to access only the S3 path we listed in the __include path__ earlier.  If you previously used AWS Glue and already created a generic service role, feel free to use it.  Next, when asked to configure the crawler output, create a new __database__ and give your source table a prefix such as __source___  Accept the rest of the defaults and save the crawler.  Now in the list of crawlers, check the checkbox next to your crawler name and click __run crawler__

Once the crawler is done a new table would be created for you in the database you selected.  Open the __Athena console__ and select the database you created from the dropdown on the left handside.  You will then see a list of tables for which you should find the one the crawler created, remember it has a prefix of source_  Click the three dots to the right of the table name and select __preview table__.  If everything went well you should see some data.
