from faker import Faker
import psycopg2
from random import choice
from datetime import datetime

fake = Faker()
conn = psycopg2.connect(
    dbname="postgres",
    user="postgresadmin",
    password="Financial_Ass1gnement",
    host="source-postgres-db.c1wii8u4iply.eu-north-1.rds.amazonaws.com",
    port="5432"
)
cur = conn.cursor()

# Insert Customers
for _ in range(20):
    cur.execute("""
        INSERT INTO customers (name, email, phone, address)
        VALUES (%s, %s, %s, %s)
    """, (
        fake.name(),
        fake.email(),
        fake.phone_number()[:20],
        fake.address()
    ))

conn.commit()  # ✅ Save customers before referencing them

# ✅ Fetch the actual customer IDs from DB
cur.execute("SELECT customer_id FROM customers")
customer_ids = [row[0] for row in cur.fetchall()]

# Insert Accounts linked to valid customer IDs
for customer_id in customer_ids:
    for _ in range(2):
        cur.execute("""
            INSERT INTO accounts (customer_id, account_type, balance, opened_at)
            VALUES (%s, %s, %s, %s)
        """, (
            customer_id,
            choice(["savings", "checking"]),
            round(fake.pyfloat(left_digits=4, right_digits=2, positive=True), 2),
            fake.date_time_between(start_date="-5y", end_date="now")
        ))

conn.commit()  # ✅ Save accounts before linking transactions

# ✅ Get actual account IDs
cur.execute("SELECT account_id FROM accounts")
account_ids = [row[0] for row in cur.fetchall()]

# Insert Transactions linked to valid accounts
for account_id in account_ids:
    for _ in range(3):
        cur.execute("""
            INSERT INTO transactions (account_id, transaction_type, amount, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (
            account_id,
            choice(["deposit", "withdrawal", "transfer"]),
            round(fake.pyfloat(left_digits=3, right_digits=2, positive=True), 2),
            fake.date_time_between(start_date="-1y", end_date="now")
        ))

conn.commit()
cur.close()
conn.close()
print("PostgreSQL database populated successfully.")
