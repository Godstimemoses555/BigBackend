import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()

api_key = os.getenv("DB_KEY")
print(f"DB_KEY present: {bool(api_key)}")

try:
    client = DataAPIClient(api_key)
    db = client.get_database_by_api_endpoint(
        "https://65602c24-7cf2-4af9-8bc6-eb24b52d36b9-us-east-2.apps.astra.datastax.com"
    )
    print("Connecting to DB...")
    colls = db.list_collection_names()
    print(f"Connection Successful! Collections: {colls}")
except Exception as e:
    print(f"CONNECTION FAILED: {e}")
