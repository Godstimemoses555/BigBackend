import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()

api_key = os.getenv("DB_KEY")
if not api_key:
    print("Error: DB_KEY not found in environment variables.")
    exit(1)

try:
    client = DataAPIClient(api_key)
    db = client.get_database_by_api_endpoint(
        "https://65602c24-7cf2-4af9-8bc6-eb24b52d36b9-us-east-2.apps.astra.datastax.com"
    )
    print("Connected to Astra DB.")
    collections = db.list_collection_names()
    print("Collections:", collections)
except Exception as e:
    print(f"Connection failed: {e}")
