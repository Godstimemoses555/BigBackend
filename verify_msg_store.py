import os
from dotenv import load_dotenv
from astrapy import DataAPIClient
import datetime

load_dotenv()
api_key = os.getenv("DB_KEY")
if not api_key:
    raise Exception("DB_KEY not found in environment variables!")

client = DataAPIClient(api_key)
db = client.get_database_by_api_endpoint(
    "https://65602c24-7cf2-4af9-8bc6-eb24b52d36b9-us-east-2.apps.astra.datastax.com"
)

if "messages" not in db.list_collection_names():
    db.create_collection("messages")

message_collection = db.get_collection("messages")

unique_content = f"VERIFY_MSG_STORE_{datetime.datetime.now().timestamp()}"

msg_data = {
    "sender_id": "test_sender",
    "receiver_id": "test_receiver",
    "content": unique_content,
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "read": False
}

print("Attempting to insert message...")
try:
    result = message_collection.insert_one(msg_data)
    print(f"Message inserted with ID: {result.inserted_id}")

    print("Attempting to retrieve message...")
    found_msg = message_collection.find_one({"_id": result.inserted_id})

    if found_msg and found_msg.get('content') == unique_content:
        print("Message retrieved successfully!")
        print(found_msg)
        # cleanup
        message_collection.delete_one({"_id": result.inserted_id})
        print("Test message cleaned up.")
    else:
        print("Failed to retrieve message correctly.")
        if found_msg:
            print(f"Found: {found_msg}")
        else:
            print("Found nothing.")

except Exception as e:
    print(f"Error during verification: {e}")
