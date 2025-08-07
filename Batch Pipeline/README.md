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

Launch an Amazon RDS for PostgreSQL instance .

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

![secretmanager](images/secretmanager.png)

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
GROUP BY
  c.name,
  c.email
ORDER BY
  total_transaction_amount DESC;

![testquery](images/testquery.png)

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


# 📊 Financial Data Warehouse & Batch ETL Pipeline

<div align="center">

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange.svg?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python)](https://python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-PySpark-red.svg?style=for-the-badge&logo=apache-spark)](https://spark.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg?style=for-the-badge&logo=postgresql)](https://postgresql.org/)

</div>

> **🎯 Project Overview:** This project demonstrates the design and implementation of a robust, serverless batch ETL pipeline on AWS. It fulfills the requirements of the Data Engineer practical assignment by ingesting data from disparate sources (PostgreSQL and DocumentDB), transforming it into an analytics-ready star schema, and loading it into a modern data lakehouse where it can be queried by BI tools.

---

## 📋 Table of Contents

- [🏗️ Architecture](#️-architecture)
- [☁️ AWS Services Used](#️-aws-services-used)
- [⚙️ Setup Instructions](#️-setup-instructions)
- [📝 Code & Process Documentation](#-code--process-documentation)
- [✅ How to Use & Verify](#-how-to-use--verify)
- [🛡️ Data Quality & Governance](#️-data-quality--governance)
- [🚧 Challenges & Solutions](#-challenges--solutions)

---

## 🏗️ Architecture

The pipeline is built on a modern, serverless **"Data Lakehouse"** architecture. This design is highly scalable, resilient, and cost-effective as it separates storage (S3) from compute (Glue, Athena).

### 🔄 Data Flow

```
Source Databases (RDS, DocumentDB) 
    ⬇️
AWS DMS (Ingestion) 
    ⬇️
Amazon S3 (Raw Zone) 
    ⬇️
AWS Glue (Catalog & ETL) 
    ⬇️
Amazon S3 (Analytics Zone) 
    ⬇️
Amazon Athena (Querying)
```

### 📊 Architecture Components

| **Component** | **Service** | **Purpose** |
|---------------|-------------|-------------|
| **Source Databases** | Amazon RDS (PostgreSQL), DocumentDB | Relational and NoSQL data sources |
| **Ingestion Layer** | AWS DMS | Full load extraction with data type conversion |
| **Raw Data Lake** | Amazon S3 `/raw/` | Landing area for unaltered data |
| **Metadata Catalog** | AWS Glue Catalog | Queryable metadata layer |
| **Transformation** | AWS Glue ETL (PySpark) | Data cleaning and star schema modeling |
| **Analytics Warehouse** | Amazon S3 `/analytics/` | Final transformed tables |
| **Query Engine** | Amazon Athena | Serverless SQL interface |

---

## ☁️ AWS Services Used

<div align="center">

| Service | Purpose | Key Features |
|---------|---------|--------------|
| ![RDS](https://img.shields.io/badge/Amazon_RDS-PostgreSQL-blue?style=flat-square) | Relational data source | Managed PostgreSQL database |
| ![DocumentDB](https://img.shields.io/badge/Amazon_DocumentDB-NoSQL-green?style=flat-square) | NoSQL data source | MongoDB-compatible document database |
| ![DMS](https://img.shields.io/badge/AWS_DMS-Migration-orange?style=flat-square) | Extract phase | Production-grade heterogeneous data ingestion |
| ![S3](https://img.shields.io/badge/Amazon_S3-Storage-red?style=flat-square) | Core storage layer | Raw data lake and analytics warehouse |
| ![Glue](https://img.shields.io/badge/AWS_Glue-ETL-purple?style=flat-square) | Transformation | Serverless Spark environment and metadata catalog |
| ![Athena](https://img.shields.io/badge/Amazon_Athena-Query_Engine-yellow?style=flat-square) | User interface | Serverless SQL query engine |

</div>

### 🔐 Security & Infrastructure

- **AWS IAM**: Role-based access control
- **AWS Secrets Manager**: Secure credential storage
- **AWS VPC & Endpoints**: Isolated network with private endpoints

---

## ⚙️ Setup Instructions

### 1. 🔑 IAM Roles & Users

- **Create IAM Role for AWS Glue** (`Glue-Project-Role`)
  - Permissions: Glue, S3, and Secrets Manager
- **Ensure DMS IAM Role** (`dms-access-for-s3`)
  - Additional permission: `s3:DeleteObject`

### 2. 🌐 VPC & Endpoints

- ✅ Provision all resources within a single VPC
- ✅ Create VPC Endpoints:
  - **S3** (Gateway)
  - **STS** (Interface)
  - **Secrets Manager** (Interface)

### 3. 🗄️ Source Databases

#### PostgreSQL Setup
- Launch Amazon RDS for PostgreSQL instance

![Create RDS](images/createrds.png)

#### DocumentDB Setup
- Launch Amazon DocumentDB cluster

![Create DocDB](images/createdocdb.jpg)

#### Connection Testing
- Test RDS connection using DBeaver

![RDS Test Connection](images/rdstestconnection.png)

- Create jumpbox (EC2 instance) for DocumentDB access

![Create Jumpbox](images/createjumpox.png)

#### Data Population
- Populate databases using scripts in `/data_population`
- Grant appropriate permissions:
  - **PostgreSQL**: `SELECT` privileges on all tables
  - **DocumentDB**: `readAnyDatabase` & `clusterMonitor` roles

#### Initial Schema Verification

![Initial Schema](images/initial-schema.png)

![Verify Documents](images/verifydocuments.png)

### 4. 🔐 Credential Management

Store database credentials in AWS Secrets Manager

![Secret Manager](images/secretmanager.png)

### 5. 🔄 AWS DMS Setup

1. **Create DMS Replication Instance** within VPC
2. **Create Source Endpoints**:
   - RDS endpoint
   - DocumentDB endpoint (linked to Secrets Manager)
3. **Create Target Endpoint** pointing to S3 bucket
4. **Create and run migration tasks**:
   - `rds-to-s3-full-load`
   - `docdb-to-s3-full-load`

![Migration Tasks Success](images/migrationtaskssuccess.png)

### 6. 🔍 AWS Glue & Athena Setup

#### Glue Database Creation
- Create Glue Database: `financial_data_db`

#### Data Cataloging
- Run `postgres-data-crawler` for relational data

![Raw Data Crawler](images/raw-crawler.png)

- Manually create `transaction_events` table schema

#### ETL Job Creation
- Create `transform-to-star-schema` Glue ETL job
- Use script from `/glue_scripts/transform-to-star-schema.py`

![Glue Job Success](images/gluejob-success.png)

#### Verify Analytics Tables

![Analytics Success](images/analytics-success.png)

#### Final Cataloging
- Run `analytics-data-crawler`

![Analytics Crawler](images/analytics-crawler.png)

#### Athena Configuration
- Configure S3 bucket for Athena query results

---

## 📝 Code & Process Documentation

### 🐍 Core ETL Script: `/glue_scripts/transform-to-star-schema.py`

#### **Phase 1: Load** 🔄
- Loads raw tables (`customers`, `accounts`, `transactions`) from Glue Catalog
- For DocumentDB data: bypasses catalog, reads directly from S3 with manual schema

#### **Phase 2: Transform** ⚙️
Creates star schema tables:

| **Table Type** | **Table Name** | **Description** |
|----------------|----------------|-----------------|
| **Dimensions** | `dim_customers` | Customer information |
|                | `dim_accounts` | Account details |
|                | `dim_dates` | Generated date dimension |
| **Facts** | `fact_transactions` | Transaction facts with foreign keys |

#### **Phase 3: Load** 💾
- Writes DataFrames to `/analytics/` S3 path in Parquet format
- Implements overwrite strategy for idempotency

---

## ✅ How to Use & Verify

### 🔍 Query Verification Steps

1. **Navigate to Amazon Athena** in AWS Console
2. **Select database**: `financial_data_db`
3. **Verify tables**: `dim_customers`, `dim_accounts`, `dim_dates`, `fact_transactions`

### 📊 Sample Analytical Query

```sql
-- Find the total transaction amount per customer
SELECT
  c.name,
  c.email,
  SUM(f.amount) AS total_transaction_amount
FROM fact_transactions AS f
JOIN dim_customers AS c
  ON f.customer_key = c.customer_key
GROUP BY
  c.name,
  c.email
ORDER BY
  total_transaction_amount DESC;
```

![Test Query](images/testquery.png)

---

## 🛡️ Data Quality & Governance

### 📈 Data Quality Measures

| **Aspect** | **Implementation** | **Benefit** |
|------------|-------------------|-------------|
| **Schema Enforcement** | Schema-on-write approach | Ensures data structure consistency |
| **Relational Integrity** | JOIN operations in ETL | Maintains referential integrity |
| **Manual Schema Control** | DocumentDB schema definition | Guarantees transformation accuracy |

### 🔒 Data Governance Framework

#### Security
- **🔐 Private VPC**: Isolated network environment
- **🛡️ VPC Endpoints**: Secure service communication
- **👤 IAM Roles**: Least-privilege permissions

#### Compliance
- **🔒 PII Processing**: Within Glue ETL job
- **⚖️ Regulation Ready**: GDPR/POPIA compliance capabilities
- **🛡️ Data Masking**: Tokenization and hashing support

---

## 🚧 Challenges & Solutions

### 🔴 Challenge 1: Service Incompatibility
**Problem**: Glue ingestion failed with PostgreSQL 17
```
❌ Initial plan: Glue for ingestion
✅ Solution: Pivoted to AWS DMS
```
**Resolution Method**: Systematic diagnosis using EC2 instance to isolate the issue

### 🔴 Challenge 2: VPC Networking Complexity
**Problem**: Service communication failures in private VPC
```
❌ Issue: Missing VPC endpoints
✅ Solution: Added STS and Secrets Manager endpoints
```
**Resolution Method**: Step-by-step network path debugging

### 🔴 Challenge 3: Schema Discovery Issues
**Problem**: Glue Crawler couldn't interpret DocumentDB Parquet schema
```
❌ Crawler approach: Unreliable schema detection
✅ Manual approach: Direct schema definition in PySpark
```
**Resolution Method**: Bypassed problematic component with manual control

---

<div align="center">

### 🎉 **Pipeline Status: Complete & Operational**

[![Build Status](https://img.shields.io/badge/Pipeline-Operational-brightgreen?style=for-the-badge)](/)
[![Data Quality](https://img.shields.io/badge/Data_Quality-Verified-blue?style=for-the-badge)](/)
[![AWS Architecture](https://img.shields.io/badge/Architecture-Serverless-orange?style=for-the-badge)](/)

</div>

---

*This documentation demonstrates a production-ready, scalable data engineering solution that successfully overcomes real-world technical challenges through systematic problem-solving and architectural best practices.*