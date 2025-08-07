Financial Data Warehouse & Batch ETL Pipeline
This project demonstrates the design and implementation of a robust, serverless batch ETL pipeline on AWS. It fulfills the requirements of the Data Engineer practical assignment by ingesting data from disparate sources (PostgreSQL and DocumentDB), transforming it into an analytics-ready star schema, and loading it into a modern data lakehouse where it can be queried by BI tools.

Table of Contents
Architecture

AWS Services Used

Setup Instructions

Code & Process Documentation

How to Use & Verify

Data Quality & Governance

Challenges & Solutions

Architecture
The pipeline is built on a modern, serverless "Data Lakehouse" architecture. This design is highly scalable, resilient, and cost-effective as it separates storage (S3) from compute (Glue, Athena).

Data Flow:
Source Databases (RDS, DocumentDB) -> AWS DMS (Ingestion) -> Amazon S3 (Raw Zone) -> AWS Glue (Catalog & ETL) -> Amazon S3 (Analytics Zone) -> Amazon Athena (Querying)

Source Databases: A PostgreSQL database on Amazon RDS holds relational data (customers, accounts), and an Amazon DocumentDB cluster holds semi-structured NoSQL data (transaction events).

Ingestion (AWS DMS): AWS Database Migration Service (DMS) performs a full load extraction from both source databases. It is a managed service that handles the connection and data type conversion, landing the raw data as Parquet files in the S3 "Raw Zone".

Raw Zone (Amazon S3): An S3 bucket (/raw/) acts as the data lake's landing area for raw, unaltered data.

Metadata Catalog (AWS Glue Catalog): An AWS Glue Crawler automatically scans the data from the PostgreSQL source, while the schema for the DocumentDB source is defined manually to ensure accuracy. This creates a queryable metadata layer over the raw data.

Transformation (AWS Glue ETL): A serverless AWS Glue ETL job, running a PySpark script, reads the raw data from the catalog. It performs joins, data cleaning, and denormalization to model the data into a star schema.

Analytics Zone (Amazon S3): The final, transformed dimension and fact tables are written by the Glue job to a clean /analytics/ prefix in S3, again in the efficient Parquet format. This is the storage layer of our data warehouse.

Data Warehouse Query Engine (Amazon Athena): Amazon Athena provides a serverless SQL interface on top of the data in the Analytics Zone. BI analysts and data scientists can connect their tools directly to Athena to query the warehouse.

AWS Services Used
Amazon RDS for PostgreSQL: Relational data source.

Amazon DocumentDB: NoSQL (MongoDB-compatible) data source.

AWS Database Migration Service (DMS): Used for the "Extract" phase. Chosen for its reliability and as a production-grade tool for heterogeneous data source ingestion.

Amazon S3: The core storage layer for both the raw data lake and the final analytics warehouse.

AWS Glue: Provides the serverless Spark environment for transformation (ETL Jobs) and the technical metadata layer (Data Catalog & Crawlers).

Amazon Athena: The serverless query engine that acts as the user-facing component of the data warehouse.

AWS IAM: Manages the necessary permissions for all services to interact securely.

AWS Secrets Manager: Securely stores and manages database credentials, avoiding hardcoding in scripts.

AWS VPC & Endpoints: Ensures the entire pipeline runs in a secure, isolated network, with private endpoints for services like S3, STS, and Secrets Manager.

Setup Instructions
IAM Roles & Users:

Create an IAM Role for AWS Glue (Glue-Project-Role) with permissions for Glue, S3, and Secrets Manager.

Ensure the IAM Role for DMS (dms-access-for-s3) has s3:DeleteObject permissions in addition to standard read/write access.

VPC & Endpoints:

Provision all resources within a single VPC.

Create VPC Endpoints for S3 (Gateway), STS (Interface), and Secrets Manager (Interface) to allow private communication between services.

Source Databases:

Launch an Amazon RDS for PostgreSQL instance (version 16 or lower is recommended for Glue compatibility).

![create-rds](images/createrds.png)

Launch an Amazon DocumentDB cluster.
![create-docdb](images/createdocdb.jpg)

Test Your connection to RDS using DBeaver(Ensure you have an inbound rule to allow your PC to access)

![rdstestconnection](images/rdstestconnection.png)

Create a jumpbox(EC2 instance to connect to Docdb)

![createjumpox](images/createjumpox.png)

Populate both databases with sample data using the scripts in /data_population. Ensure the DMS database user has been granted SELECT privileges on all tables in PostgreSQL and the readAnyDatabase & clusterMonitor roles in DocumentDB.

Your Initial Schema should e like 

![initial-schema](images/initial-schema.png)

Verify Your Docdb is populated

![verifydocuments](images/verifydocuments.png)

Credential Management:

Store the credentials for both RDS and DocumentDB in AWS Secrets Manager.

![secretmanager](images/secretmanager.jpg)

AWS DMS Setup:

Create a DMS Replication Instance within the VPC.

Create a Source Endpoint for RDS and another for DocumentDB, linking them to their respective secrets in Secrets Manager.

Create a Target Endpoint pointing to your S3 bucket.

Create and run the two migration tasks (rds-to-s3-full-load and docdb-to-s3-full-load).

![migrationtaskssuccess](images/migrationtaskssuccess.png)

AWS Glue & Athena Setup:

Create a Glue Database named financial_data_db.

Create and run the postgres-data-crawler to catalog the relational data.

![Raw data crawler](images/raw-crawler.png)

Manually create the transaction_events table in the catalog to ensure a correct schema.

Create the transform-to-star-schema Glue ETL job using the script from /glue_scripts/transform-to-star-schema.py.

Run the transformation job.

![gluejob-success](images/gluejob-success.png)

Verify dim and Fact tables are created

![analytics-success](images/analytics-success.png)

Create and run the final analytics-data-crawler to catalog the transformed tables.

![analytics-crawler](images/analytics-crawler.png)


Configure an S3 bucket for Athena query results.

Code & Process Documentation
/glue_scripts/transform-to-star-schema.py: This is the core logic of the pipeline.

Load Phase: It begins by loading the raw tables (customers, accounts, transactions) from the Glue Catalog. For the problematic DocumentDB data, it bypasses the catalog and reads directly from S3, applying a manually defined schema in the code to guarantee correctness.

Transformation Phase: It uses PySpark to build the dimension and fact tables.

dim_customers & dim_accounts are created by selecting and renaming columns.

dim_dates is a generated dimension, created by extracting the distinct dates from the transaction timestamps.

fact_transactions is built by performing a series of join operations to link the source tables together and enrich the transaction data. Ambiguous column references (like timestamp and account_id) are explicitly resolved to prevent errors.

Load Phase: The final DataFrames are written out to the /analytics/ S3 path in Parquet format, overwriting any previous data to ensure idempotency.

How to Use & Verify
Run the entire pipeline as described in the Setup Instructions.

Navigate to Amazon Athena in the AWS Console.

Select the financial_data_db from the Database dropdown.

Verify the tables: You should see dim_customers, dim_accounts, dim_dates, and fact_transactions on the left.

Run analytical queries to test the model. Example:

-- Find the total transaction amount per customer
SELECT
  c.name,
  c.email,
  SUM(f.amount) AS total_transaction_amount
FROM fact_transactions AS f
JOIN dim_customers AS c
  ON f.customer_key = c.customer_key
GROUP BY 1, 2
ORDER BY 3 DESC;

Data Quality & Governance
Data Quality:

Schema Enforcement: The pipeline enforces a strict schema-on-write approach. The manually defined schema for the DocumentDB data and the crawled schema for the PostgreSQL data ensure that only data conforming to the expected structure is processed.

Relational Integrity: The JOIN operations in the Glue script act as an implicit quality check, dropping any records that fail to join and thus ensuring the referential integrity of the final star schema.

Data Governance:

Security: The entire architecture is secured using a private VPC, VPC Endpoints, and IAM roles with least-privilege permissions.

Compliance: Sensitive PII (like email and address) is processed within the Glue ETL job, which is the ideal place to apply hashing, masking, or tokenization functions before loading the data into the final warehouse, ensuring compliance with regulations like GDPR or POPIA.

Challenges & Solutions
This project involved overcoming several realistic, complex engineering challenges, demonstrating a systematic approach to debugging.

Challenge 1: Service Incompatibility: The initial plan to use Glue for ingestion failed due to an incompatibility between Glue's drivers and the new PostgreSQL 17.

Solution: I diagnosed this by using an EC2 instance to prove the network path was valid, which isolated the problem to Glue itself. I then pivoted to a more robust and appropriate tool for the job, AWS DMS, which successfully handled the ingestion.

Challenge 2: Complex VPC Networking: The services initially failed to communicate within the private VPC.

Solution: I systematically debugged the network path, adding necessary VPC Endpoints for STS and Secrets Manager, and corrected the Security Group rules to allow traffic between the services on the required ports.

Challenge 3: Flawed Schema Discovery: The Glue Crawler repeatedly failed to correctly interpret the schema of the Parquet files generated from the DocumentDB source.

Solution: After multiple attempts to fix the crawler failed, I switched to a more resilient strategy. I bypassed the crawler for the problematic source and defined the schema manually within the PySpark script. This provided complete control and guaranteed the transformation job would succeed.