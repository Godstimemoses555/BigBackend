import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()

api_key = os.getenv("DB_KEY")
if not api_key:
    raise Exception("DB_KEY not found in environment variables!")

client = DataAPIClient(api_key)
db = client.get_database_by_api_endpoint(
    "https://65602c24-7cf2-4af9-8bc6-eb24b52d36b9-us-east-2.apps.astra.datastax.com"
)

print("Collections:", db.list_collection_names())

users_col = db.get_collection("users")
# List users
print("\nUsers in DB:")
try:
    users = list(users_col.find({}))
    for u in users:
        print(f"ID: {u['_id']}, Email: {u.get('Email')}")
except Exception as e:
    print(f"Error listing users: {e}")
