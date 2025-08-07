import json
import boto3
import os
from datetime import datetime
from decimal import Decimal


# Explicitly define the region for the DynamoDB client.
DYNAMO_REGION = "eu-north-1"
dynamodb = boto3.resource('dynamodb', region_name=DYNAMO_REGION)
# -----------------------

TABLE_NAME = "RealTimeTransactions"
table = dynamodb.Table(TABLE_NAME)

# (Replace floats with decimals to avoid errors in Dynamo)

def replace_floats_with_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_floats_with_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = replace_floats_with_decimals(v)
        return obj
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def lambda_handler(event, context):
    print(f"Received {len(event['Records'])} records from SQS.")

    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            item_to_store = replace_floats_with_decimals(message_body)
            
            amount = item_to_store.get('amount', 0)
            if amount > 10000:
                item_to_store['transaction_category'] = 'high_value'
            elif amount > 500:
                item_to_store['transaction_category'] = 'medium_value'
            else:
                item_to_store['transaction_category'] = 'standard_value'
            
            item_to_store['processed_at_utc'] = datetime.utcnow().isoformat()
            
            table.put_item(Item=item_to_store)
            
            print(f"Successfully processed and stored transaction_id: {item_to_store['transaction_id']}")

        except Exception as e:
            # Log any errors
            print(f"An error of type {type(e).__name__} occurred: {e}")
            continue
            
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete!')
    }