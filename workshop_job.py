import os
import sys
import boto3

from awsglue.job import Job
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions

import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.context import SparkContext

## import Comprehend API functions wrapped as Spark UDFs
from comprehend_api import getSentiment

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

AWS_REGION = 'us-east-1'
MIN_SENTENCE_LENGTH_IN_CHARS = 10
MAX_SENTENCE_LENGTH_IN_CHARS = 4500  ## API supports max 5000 bytes, 1char ~ 1byte
ROW_LIMIT = 10

## Read source Amazon product review dataset from pre-crawled table in Glue Data Catalog
#TODO: Change the database and table names to reflect those in your data catalog
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "<BD_NAME>", table_name = "<TABLE_NAME>", transformation_ctx = "datasource0")

## Convert from Glue DynamicFrame to Spark DataFrame
reviews = datasource0.toDF()

## Filter down dataset to only those reviews that we expect will return a meaningful result
df = reviews \
  .where("marketplace = 'US'") \
  .where((F.length('review_body') > MIN_SENTENCE_LENGTH_IN_CHARS) & (F.length('review_body') < MAX_SENTENCE_LENGTH_IN_CHARS)) \
  .limit(ROW_LIMIT)

## Call Comprehend API to perform NLP on review text and add results as column to the dataset
df2 = df \
  .withColumn('sentiment', getSentiment(df.review_body)) \
  .drop('review_body')

## Write out result set to S3 in Parquet format
## TODO: update the S3 path with your own
df2.write \
  .mode('overwrite') \
  .parquet('s3://<YOUR_BUCKET/reinvent/aim416/output/parquet')

job.commit()
