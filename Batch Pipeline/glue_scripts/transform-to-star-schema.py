
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, year, month, dayofmonth, date_format, to_date
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType

# --- 1. INITIALIZATION ---
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# --- CONFIGURATION ---
source_database = "financial_data_db" 
s3_output_path = "s3://equals-project-data-2025/analytics/" 
s3_events_path = "s3://equals-project-data-2025/raw/financialdb/transaction_events/"

# --- 2. LOAD DATA ---
print("Loading raw data...")

# Load the clean PostgreSQL data from the Glue Catalog
customers_df = glueContext.create_dynamic_frame.from_catalog(database=source_database, table_name="customers").toDF()
accounts_df = glueContext.create_dynamic_frame.from_catalog(database=source_database, table_name="accounts").toDF()
transactions_df = glueContext.create_dynamic_frame.from_catalog(database=source_database, table_name="transactions").toDF()

# Define the correct schema for the events data
events_schema = StructType([
    StructField("transaction_id", LongType(), True),
    StructField("device_type", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("geolocation", StructType([
        StructField("country", StringType(), True),
        StructField("city", StringType(), True)
    ]), True),
    StructField("fraud_score", DoubleType(), True)
])

# Read the Parquet files from S3 using the manually defined schema
print(f"Reading events data directly from {s3_events_path}")
events_df = spark.read.schema(events_schema).parquet(s3_events_path)
print("Events data successfully loaded from S3.")


# --- 3. CREATE DIMENSION TABLES ---

print("Creating dim_customers...")
dim_customers = customers_df.select(
    col("customer_id").alias("customer_key"), col("name"), col("email"), col("address"), col("phone")
)
dim_customers.write.mode("overwrite").parquet(f"{s3_output_path}/dim_customers/")
print("dim_customers successfully written to S3.")

print("Creating dim_accounts...")
dim_accounts = accounts_df.select(
    col("account_id").alias("account_key"), col("customer_id").alias("customer_key"), col("account_type"), col("opened_at"), col("balance")
)
dim_accounts.write.mode("overwrite").parquet(f"{s3_output_path}/dim_accounts/")
print("dim_accounts successfully written to S3.")

print("Creating dim_dates...")
dim_dates = transactions_df.select(transactions_df["timestamp"]).distinct().select(
    to_date(col("timestamp")).alias("date")
).distinct()
dim_dates = dim_dates.select(
    col("date"), date_format(col("date"), "yyyyMMdd").cast("int").alias("date_key"),
    year(col("date")).alias("year"), month(col("date")).alias("month"), dayofmonth(col("date")).alias("day")
)
dim_dates.write.mode("overwrite").parquet(f"{s3_output_path}/dim_dates/")
print("dim_dates successfully written to S3.")


# --- 4. CREATE FACT TABLE ---


print("Creating fact_transactions...")
facts = transactions_df.join(accounts_df, "account_id")
facts = facts.join(events_df, "transaction_id", "left_outer")
facts = facts.withColumn("date_key", date_format(to_date(transactions_df["timestamp"]), "yyyyMMdd").cast("int"))

fact_transactions = facts.select(
    transactions_df["transaction_id"], col("date_key"),
    accounts_df["account_id"].alias("account_key"), accounts_df["customer_id"].alias("customer_key"),
    transactions_df["amount"], transactions_df["transaction_type"],
    events_df["device_type"], events_df["fraud_score"]
)
fact_transactions.write.mode("overwrite").parquet(f"{s3_output_path}/fact_transactions/")
print("fact_transactions successfully written to S3.")

job.commit()