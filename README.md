# AIM416 Build an ETL pipeline to analyze customer data
## Introduction
In this workshop we will use AWS Glue ETL to enrich [Amazon Product Review dataset](https://registry.opendata.aws/amazon-reviews/).  To do that we will pass the product review text to [Amazon Comprehend](https://aws.amazon.com/comprehend/) to detect sentiment, extract entities and key phrases which will be added to the original review dataset.  We will then save the dataset to Amazon S3 in Apache Parquet format so it can be quiered with [Amazon Athena](https://aws.amazon.com/athena/) and visualized with [Amazon QuickSight](https://aws.amazon.com/quicksight/).

**NOTE: This workshop assumes you are running in us-east-1 region.  If you prefer to run in another region you will need to update the accompanying scripts.  Also be warned that the Amazon product review dataset is hosted in us-east-1, accessing it from another region may inccur additional data transfer costs.**

## Helpful links
1. [Apache Spark API documentation](http://spark.apache.org/docs/2.2.1/api/python/pyspark.sql.html)
2. [Amazon Comprehend Boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/comprehend.html#id30)

## Authorization and permissions
Before we can start we need to define the appropriate policies and permissions for the differnet services to use.  In this workshop I assume you are logged in as a root user or a user with enough privileges to be able to create IAM roles and assign policies.  If you don't have that level of permission, either ask the owner of your account to help or create a personal account where you have more permission.

If you get stuck, there is more information here:
1. [Setting up IAM Permissions for AWS Glue](https://docs.aws.amazon.com/glue/latest/dg/getting-started-access.html)
2. [Overview of Managing Access Permissions for Amazon Comprehend Resources](https://docs.aws.amazon.com/comprehend/latest/dg/access-control-overview.html)

### Create AWS Glue service role
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
Start by downloading [__comprehend_api.py__](https://raw.githubusercontent.com/rhasson/reinvent2018_aim416/master/comprehend_api.py) to your local computer.  Then open the AWS Console and navigate to the S3 console.  If you don't already have one, create a bucket with a unique name.  S3 uses a flat namespace which means bucket names must be unique across all S3 customers.  Inside the bukcet, create a subfolder and name it __deps__ and upload __comprehend_api.py__ into the deps folder.  The __comprehend_api.py__ file includes a few functions that allow us to take a row field from our dataset and pass it to the Comprehend API.  
For this function to work as a UDF (user defined function) in [Apache Spark](http://spark.apache.org/docs/2.2.1/api/python/pyspark.sql.html) which AWS Glue uses under the hood, we need to wrap our function in a special UDF function factory.  To simplify our code for reability and extensibility we broke out these functions into their own file.

## Crawling Source Dataset
The next thing we need to do is use AWS Glue crawler to discover and catalog our source dataset which will then create a schema for us in the AWS Glue Data Catalog.  Open the AWS Glue console and navigate to __Crawlers__ under the __Data Catalog__ section on the left side of the console.  Click on __Add Crawler__ and follow the wizard accepting all of the defaults.  When it asks you to specific an __Include Path__ select __specficied path in another account__ and enter __s3://amazon-reviews-pds/parquet/__ in the include path text box.  Next, when asked to __choose an IAM role__ select __create an IAM role__ and give it a name.  Note that does role will create IAM S3 policies to access only the S3 path we listed in the __include path__ earlier.  If you previously used AWS Glue and already created a generic service role, feel free to use it.  Next, when asked to configure the crawler output, create a new __database__ and give your source table a prefix such as __source___  Accept the rest of the defaults and save the crawler.  Now in the list of crawlers, check the checkbox next to your crawler name and click __run crawler__

Once the crawler is done a new table would be created for you in the database you selected.  Open the __Athena console__ and select the database you created from the dropdown on the left handside.  You will then see a list of tables for which you should find the one the crawler created, remember it has a prefix of source_  Click the three dots to the right of the table name and select __preview table__.  If everything went well you should see some data.

## Creating AWS Glue ETL job
The next thing we need to do is create an AWS Glue ETL job that when executed will read the product review dataset, enrich it with Comprehend and write it back out into S3 so we can later analyze and visual the results.  Open the __Glue console__ and select __Jobs__ from the left hand side.  Click __Add Job__ and follow along with the wizard.  For the __IAM Role__ select the role you created earlier.  Select the __A new script to be authored by you__ in the __This job runs__ sections.  Under the __Advanced Properties__ dropdown enable __Job metrics__.  Under the __Security configuration, script libraries and job parameters__ dropdown, enter the full S3 path to the __comprehend_api.py__ you uploaded previously in the __Python library path__ textbox, i.e. s3://my-bucket/aim416/deps/comprehend_api.py
Further down under __Concurrent DPUs per job run__ change it to __5__.  A Data Processing Unit or DPU is a measure of resources that we can assign to our job.  A single DPU equates to 4 CPU cores and 16GB of memory.  For this excercise and to reduce cost, 5 DPU is sufficient.  Continue on with the wizard accepting the defaults and finally save the job.

### Editing the ETL script
Now that your job has been created, you should have the ETL script editor open in the console.  Select all of the text in the current script and delete it.  Come back to this repo, open [__workshop_job.py__](https://raw.githubusercontent.com/rhasson/reinvent2018_aim416/master/workshop_job.py) and copy its contents and paste them into the AWS Glue ETL script editor.  Click __save__.  Review the script and note the __TODO__ comments and make the appropriate changes to the script.

As you will see, the script does the following:
1. Read the raw dataset as defined by the AWS Glue Data Catalog
2. Filters the dataset to only return rows for the US marketplace (so we have English only text), where the review is long enough to have meaningul results and finally grabs only a few rows so we can quickly see results.
3. We add a column called __sentiment__ that will hold the sentiment value detected by Comprehend on our review text.  The __getSentiment__ function is declared in __comprehend_api.py__
4. We drop the __review_body__ from the results just to make it easier to explore the resulting table but you can remove that line if you like
5. We write the result dataset to S3 in Apache Parquet format

### Querying our results
Once the script finish executing the output Parquet data will be in the S3 location you defined in the script.  We will now need to create another AWS Glue crawler to discover and catalog our new data.  Follow the previous instructions to create a crawler.  Make sure you create a __new__ IAM role so it has permissions to access your output location.  Once completed, open the __Athena console__, select your table and preview it.  Scroll all the way to the right side to see the new sentiment column.

## Next Steps
Assuming you completed all of the previous steps you should be ready to move forward with exploring how we can further leverage Comprehend to enrich our dataset.
### Step 1
As you may have already noticed I included a __getEntities__ function in the __comprehend_api.py__ file that you should now add to your ETL script.  Go ahead and try importing it and adding it to your script, similar to how __getSentiment__ is used in the __withColumn__ API.  Note that once the new data is written to S3 (same output location), you will need to first delete the old table in AWS Glue Data Catalog and then rerun the crawler so it can a new table with the new schema.
### Step 2
Amazon Comprehend also includes an API to extract key phrases from text.  I've created a skeleton UDF in comprehend_api.py to get you started.  In this part of the workshop, go ahead and implement the __getKeyPhrases__ UDF.  You will need to edit comprehend_api.py on your local machine, make the code changes and upload it back to S3.  You can either overwrite the existing file or upload it under a different name.  Don't forget to confirm you have the correct path and filename under in __Python library path__ field of the job settings.
### Step 3
The product review dataset has reviews in other languages.  Both German (DE) and French (FR) are supported by Comprehend and are also available in our dataset.  In your AWS Glue ETL script create another DataFrame representing only German lanuage reviews.  You then need to further extend the comprehend_api.py UDFs to allow you to pass a second parameter representing the lanuage.  Go ahead and try this with Sentiment analysis and see what you get.
### Step 4
Open Amazon [QuickSight](https://aws.amazon.com/quicksight/) and configure appropriate [IAM permissions](https://docs.aws.amazon.com/quicksight/latest/user/managing-permissions.html).  Once setup, add a Data Set representing the table we created in Step 3.  Go ahead and explore creating visualizations beased on the data.
