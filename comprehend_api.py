import os
import sys
import boto3

import pyspark.sql.functions as F
from pyspark.sql.types import *

AWS_REGION = 'us-east-1'


## Define Spark schema for the returned results from Comprehend detect_sentiment API
sentiment_schema = StringType()

## UDF for getting a sentiment value of the passed in text string using Comprehend detect_sentiment API
@F.udf(returnType=sentiment_schema)
def getSentiment(text):
  client = boto3.client('comprehend',region_name = AWS_REGION)

  def callApi(t):
    response = client.detect_sentiment(Text = t, LanguageCode = 'en')
    return response

  r = callApi(text)

  return str(r['Sentiment'])

## Define Spark schema for the returned results from Comprehend detect_entities API
entities_schema = ArrayType(StructType() \
  .add("text", StringType(), True) \
  .add("score", DoubleType(), True) \
  .add("type", StringType(), True))

## UDF for getting entities from the passed in text string using Comprehend detect_entities API
@F.udf(returnType=entities_schema)
def getEntities(text):
  client = boto3.client('comprehend',region_name = AWS_REGION)

  def callApi(t):
    response = client.detect_entities(Text = t, LanguageCode = 'en')
    return response

  r = callApi(text)
  
  data = []
  for i in r['Entities']: data.append(dict((k.lower(), v) for k, v in i.items()))
  
  return data

## Define Spark schema for the returned results from Comprehend detect_key_phrases API
# TODO: complete schema definition (hint - review entities_schema)
# API description: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/comprehend.html#Comprehend.Client.detect_key_phrases
phrases_schema = ArrayType(StructType() \
  .add("text", StringType(), True) \
  .add("score", DoubleType(), True))

## UDF for getting entities from the passed in text string using Comprehend detect_key_phrases API
@F.udf(returnType=phrases_schema)
def getKeyPhrases(text):
  client = boto3.client('comprehend',region_name = AWS_REGION)

  def callApi(t):
    response = client.detect_key_phrases(Text = t, LanguageCode = 'en')
    return response

  r = callApi(text)
  
  # TODO: return results set
  data = []
  
  return data