
from astrapy import DataAPIClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
# Connect to Astra DB
client = DataAPIClient(
    database_id=os.getenv("DB_ID"),
    database_region=os.getenv("DB_REGION"),
    auth_token=os.getenv("DB_KEY")
)

load_dotenv()


users_table = "users"

# Your dummy users
dummy_users = [
    {"name": "Johne Deo", "age": 22, "Email": "johne.deo@example.com", "password": "password123"},
    {"name": "Bassey Bassey", "age": 22, "Email": "bassey.bassey@example.com", "password": "password123"},
    {"name": "Moses Alade", "age": 22, "Email": "moses.alade@example.com", "password": "password123"},
    {"name": "Mark Zuddy", "age": 22, "Email": "mark.zuddy@example.com", "password": "password123"},
    {"name": "David Ahams", "age": 22, "Email": "david.ahams@example.com", "password": "password123"}
]

# Check if table is empty
existing_users = client.table(users_table).get()
if existing_users["count"] == 0:
    for user in dummy_users:
        client.table(users_table).insert(user)
    print("Dummy users inserted successfully!")
else:
    print("Users already exist. No action taken.")
