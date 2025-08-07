import boto3
import json
import time
import random
import uuid
from datetime import datetime

# Configure the SQS client
sqs = boto3.client('sqs', region_name='eu-north-1') 

# The URL of the SQS queue 
QUEUE_URL = 'https://sqs.eu-north-1.amazonaws.com/114894399234/FinancialTransactionQueue'

def generate_transaction_data():
    """Generates a single fake financial transaction."""
    return {
        'transaction_id': str(uuid.uuid4()),
        'user_id': f'user_{random.randint(100, 999)}',
        'amount': round(random.uniform(5.50, 25000.00), 2),
        'currency': 'USD',
        'transaction_timestamp_utc': datetime.utcnow().isoformat(),
        'merchant': random.choice(['Amazon', 'Apple', 'Shell', 'Walmart', 'BestBuy'])
    }

def send_to_sqs(data):
    """Sends a dictionary as a JSON message to the SQS queue."""
    try:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        print(f"Message sent! ID: {response['MessageId']}, Transaction ID: {data['transaction_id']}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    print("Starting financial data producer...")
    while True:
        transaction = generate_transaction_data()
        send_to_sqs(transaction)
        # Waiting for a random interval to simulate real-world traffic
        time.sleep(random.uniform(0.5, 3.0))