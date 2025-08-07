Real-Time Financial Transaction Analytics Pipeline
This project demonstrates a serverless, event-driven data pipeline on AWS for ingesting, processing, and analyzing simulated financial transactions in near-real-time. The entire infrastructure is designed to be compliant with the AWS Free Tier, showcasing a cost-effective approach to streaming data challenges.

Table of Contents
Architecture

AWS Services Used

Setup Instructions

Code Documentation

How to Use

Challenges & Solutions

Architecture
The pipeline follows a decoupled, serverless architecture that is highly scalable and resilient.

Data Flow:
EC2 Instance (Producer) -> Amazon SQS (Queue) -> AWS Lambda (Processor) -> Amazon DynamoDB (Datastore)

!(https://www.google.com/search?q=https://i.imgur.com/9O1nL5E.png)

Producer (financial_producer.py): A Python script running on an EC2 t2.micro instance generates simulated financial transaction data (e.g., transaction ID, amount, merchant).

Ingestion & Buffering (Amazon SQS): The producer sends each transaction as a message to an SQS Standard Queue. SQS acts as a durable buffer, decoupling the producer from the processing logic and ensuring no data is lost if the processing layer is temporarily unavailable.

Processing & Transformation (AWS Lambda): An AWS Lambda function is automatically triggered by new messages arriving in the SQS queue. The function reads the message, performs a simple transformation (categorizing the transaction as 'high_value', 'medium_value', or 'standard'), and adds a processing timestamp.

Analytics Datastore (Amazon DynamoDB): The enriched data record is then stored in a DynamoDB table, which is a NoSQL database optimized for low-latency read/write operations, making it ideal for real-time analytics dashboards.

AWS Services Used
Amazon EC2 (t2.micro): Hosts the data producer script. Chosen for its inclusion in the AWS Free Tier.

Amazon SQS (Standard Queue): Serves as the message broker. Chosen as a cost-effective, serverless alternative to Kinesis Data Streams.

AWS Lambda: Provides the serverless compute layer for real-time data processing.

Amazon DynamoDB: Used as the target NoSQL data store for the processed records.

AWS IAM: Manages the necessary permissions for AWS services to interact with each other securely.

Amazon CloudWatch: Used for logging and monitoring the Lambda function's execution.

Setup Instructions
1. IAM Roles
Create two IAM Roles:

EC2 Role (EC2-SQS-Role):

Trusted Entity: EC2

Permissions: AmazonSQSFullAccess (In a production environment, this should be restricted to sqs:SendMessage on the specific queue ARN).

Lambda Role (Lambda-SQS-DynamoDB-Role):

Trusted Entity: Lambda

Permissions: AWSLambdaSQSQueueExecutionRole and AmazonDynamoDBFullAccess (In production, restrict to dynamodb:PutItem on the specific table ARN).

2. Amazon SQS Queue
Create a Standard SQS queue named FinancialTransactionQueue.

Note the Queue URL after creation.

3. Amazon DynamoDB Table
Create a DynamoDB table named RealTimeTransactions.

Set the Partition key to transaction_id (Type: String).

4. AWS Lambda Function
Create a Lambda function named ProcessFinancialStream.

Runtime: Python 3.9+

Execution Role: Attach the Lambda-SQS-DynamoDB-Role created in Step 1.

Add Trigger: Configure an SQS trigger pointing to the FinancialTransactionQueue.

Code: Paste the contents of lambda/lambda_function.py into the code editor and deploy.

5. EC2 Instance
Launch a t2.micro EC2 instance using the Amazon Linux 2023 AMI.

IAM Instance Profile: Attach the EC2-SQS-Role created in Step 1.

SSH into the instance, install Boto3 (pip3 install boto3), and upload the producer/financial_producer.py script.

Code Documentation
producer/financial_producer.py
This script simulates a stream of financial transactions.

It generates a random transaction record containing a UUID, user ID, amount, currency, timestamp, and merchant.

It converts this record into a JSON string.

It sends the JSON string as a message to the specified SQS Queue URL.

It runs in an infinite loop with a random sleep interval to mimic a real-world data stream.

lambda/lambda_function.py
This is the core processing logic for the pipeline.

It is configured to be triggered by messages from SQS.

For each record, it parses the JSON message body.

Crucially, it converts any float data types (like the transaction amount) into Python's Decimal type, which is required by DynamoDB for high-precision numbers.

It performs a simple analytical transformation by adding a transaction_category key based on the transaction amount.

It adds a processed_at_utc timestamp.

It writes the final, enriched item to the RealTimeTransactions DynamoDB table using table.put_item().

It includes try...except blocks for robust error logging in CloudWatch.

How to Use
Ensure all AWS resources are set up as described above.

Update the QUEUE_URL variable in financial_producer.py with your SQS queue URL.

Run the producer script from your EC2 instance's terminal: python3 financial_producer.py.

Verification:

Watch the real-time logs in CloudWatch for the ProcessFinancialStream Lambda function to see "Successfully processed..." messages.

Go to the DynamoDB console, select the RealTimeTransactions table, and click Explore table items to see the new data arriving.

Challenges & Solutions
During development, two key challenges were encountered and resolved:

Constraint: The AWS Free Tier does not include Kinesis Data Streams, the standard service for this use case.

Solution: A serverless alternative was designed using SQS as a message buffer and Lambda for event-driven processing. This achieved the same outcome in a highly cost-effective and scalable manner.

Technical Error: The Lambda function initially failed with the error Float types are not supported. Use Decimal types instead.

Solution: The error was diagnosed using CloudWatch logs. The Lambda code was modified to import Python's Decimal library and explicitly convert all floating-point numbers to the Decimal type before attempting to write them to DynamoDB, ensuring data precision and compatibility.