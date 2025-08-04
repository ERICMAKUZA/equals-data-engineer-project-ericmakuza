
import pymongo
from faker import Faker
from random import choice, randint

# ✅ FIX 1: Create an instance of the Faker class
fake = Faker()

# Connect to the local end of the tunnel
CONNECTION_STRING = "mongodb://admin01:Financial_Ass1gnement@source-docdb-cluster.cluster-c1wii8u4iply.eu-north-1.docdb.amazonaws.com:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"

client = pymongo.MongoClient(
    CONNECTION_STRING,
    tls=True,
    tlsCAFile='global-bundle.pem',
    # ✅ FIX 2: Allow connection despite hostname mismatch
    tlsAllowInvalidHostnames=True
)

db = client.financialdb
events_collection = db.transaction_events

print("Populating DocumentDB via EC2 Instance...")

# Create 120 event documents
for i in range(1, 121):
    event = {
        "transaction_id": i,
        "device_type": choice(["mobile_app", "web_browser", "atm"]),
        "ip_address": fake.ipv4(),
        "geolocation": {
            "country": fake.country(),
            "city": fake.city(),
        },
        "fraud_score": round(randint(1, 100) / 100, 2)
    }
    events_collection.insert_one(event)

client.close()

print("DocumentDB populated successfully.")