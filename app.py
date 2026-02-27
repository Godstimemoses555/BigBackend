from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
# from fastapi import FastAPI, UploadFile, File, Form
from dotenv import load_dotenv
from astrapy import DataAPIClient
from fastapi.responses import JSONResponse
import base64
import uuid
from fastapi.middleware.cors import CORSMiddleware
from utility import (
    hashedpassword,
    verifyHashed,
    hash_secret_pin,
    verify_secret_pin
)
from model import Login, User, CreateSecretPin, Message

from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

def every_5_mins_job():
    print(f"[{datetime.utcnow().isoformat()}] Running 5-minute background job...")
    # Add your 5 minute periodic task logic here
    pass

def daily_job():
    print(f"[{datetime.utcnow().isoformat()}] Running daily background job...")
    # Add your daily periodic task logic here (runs at midnight)
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the scheduler
    scheduler = BackgroundScheduler()
    
    # Schedule job every 5 minutes
    scheduler.add_job(every_5_mins_job, 'interval', minutes=5)
    
    # Schedule daily job at midnight (00:00)
    scheduler.add_job(daily_job, 'cron', hour=0, minute=0)
    
    # Start the scheduler
    scheduler.start()
    print("Background scheduler started.")
    
    yield  # Application runs here
    
    # Shutdown the scheduler when the app stops
    scheduler.shutdown()
    print("Background scheduler shutdown.")

load_dotenv()

app = FastAPI(lifespan=lifespan)

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # FIXED
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# -------------------- Astra DB --------------------
api_key = os.getenv("DB_KEY")
if not api_key:
    raise Exception("DB_KEY not found in environment variables!")

client = DataAPIClient(api_key)
db = client.get_database_by_api_endpoint(
    "https://65602c24-7cf2-4af9-8bc6-eb24b52d36b9-us-east-2.apps.astra.datastax.com"
)

if "users" not in db.list_collection_names():
    db.create_collection("users")

if "messages" not in db.list_collection_names():
    db.create_collection("messages")

user_collection = db.get_collection("users")
message_collection = db.get_collection("messages")

# -------------------- ROUTES --------------------
@app.get("/")
async def home():
    return {"message": "Welcome to MoshChat FastAPI!"}


@app.post("/create")
async def create_user(user: User):
    data = dict(user)
    data["Email"] = data["Email"].strip().lower() # normalize email
    if user_collection.find_one({"Email": data["Email"]}):
        return JSONResponse({"message": "User already exists"}, status_code=400)

    data["password"] = hashedpassword(data["password"])
    data["pin_hash"] = None
    data["pin_enabled"] = False
    data["is_active"] = False

    result = user_collection.insert_one(data)
    return JSONResponse({"message": "User created successfully", "user_id": str(result.inserted_id)}, status_code=201)

@app.post("/set_pin")
async def set_secret_pin(data1: CreateSecretPin):
    try:
        data = dict(data1)

        email = data["Email"].strip().lower()
        print("Normalized Email:", email)

        user = user_collection.find_one(
            filter={"Email": email}
        )

        if user:
            hashed_pin = hash_secret_pin(data["secretpin"])

            user_collection.find_one_and_update(
                filter={"Email": email},
                update={"$set": {
                    "pin_hash": hashed_pin,
                    "pin_enabled": True
                }}
            )

            return JSONResponse(
                {"message": "Secret PIN set successfully"},
                status_code=200
            )

        return JSONResponse(
            {"message": "User not found"},
            status_code=404
        )

    except Exception as e:
        print("SET PIN ERROR:", str(e))
        return JSONResponse(
            {"message": "Server error", "error": str(e)},
            status_code=500
        )




@app.post("/login")
async def login_user(login: Login):
    data = dict(login)
    Email = str(data["Email"]).strip().lower()  # normalize email
    pin = str(data["secretpin"]).strip()        # normalize pin

    # Find user by normalized Email
    user = user_collection.find_one({"Email": Email})
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)

    if not user.get("pin_enabled") or not user.get("pin_hash"):
        return JSONResponse({"message": "PIN not set"}, status_code=403)

    # Verify PIN with proper hash comparison
    if not verify_secret_pin(pin, user["pin_hash"]):
        return JSONResponse({"message": "Invalid Secret PIN"}, status_code=401)

    # Mark user as active
    user_collection.find_one_and_update({"Email": Email}, {"$set": {"is_active": True}})

    return JSONResponse(
        {"message": "Login successful", "user_id": str(user["_id"])},
        status_code=200
    )




@app.put("/update_profile")
async def update_profile(data: dict):
    try:
        # Get and normalize email
        raw_email = data.get("Email")
        if not raw_email:
            return JSONResponse({"message": "Email is required"}, status_code=400)
        
        email = raw_email.strip().lower()
        
        # Verify user exists FIRST
        user = user_collection.find_one({"Email": email})
        if not user:
            print(f"DEBUG: User not found for email: '{email}'")
            return JSONResponse({"message": f"User with email {email} not found"}, status_code=404)

        # Prepare update data
        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        profile_image = data.get("profile_image") 

        update_data = {}
        if name: update_data["name"] = name
        if age is not None:
            try:
                update_data["age"] = int(age)
            except (ValueError, TypeError):
                return JSONResponse({"message": "Invalid age format"}, status_code=400)
        if gender: update_data["gender"] = gender

        # Handle Image
        if profile_image and profile_image.startswith("data:"):
            import uuid, os, base64
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            try:
                header, base64_data = profile_image.split(",", 1)
                image_bytes = base64.b64decode(base64_data)
                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join(UPLOAD_DIR, filename)

                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                # Store the relative path in DB
                update_data["profile_image"] = f"/{UPLOAD_DIR}/{filename}"
            except Exception as img_err:
                print("IMAGE PROCESSING ERROR:", str(img_err))
                return JSONResponse({"message": "Failed to process image"}, status_code=400)
        elif profile_image:
            # If it's already a path, keep it
            update_data["profile_image"] = profile_image

        if not update_data:
            return JSONResponse({"message": "No data to update"}, status_code=400)

        # Execute Update
        user_collection.update_one({"Email": email}, {"$set": update_data})

        # Fetch updated user for response
        updated_user = user_collection.find_one({"Email": email})
        
        # Format for response
        if updated_user:
            updated_user["_id"] = str(updated_user["_id"])
            # Ensure profile_image is a full URL if it exists
            if updated_user.get("profile_image") and updated_user["profile_image"].startswith("/"):
                # Use hardcoded IP matching your current network setup
                server_ip = "192.168.56.219" 
                updated_user["profile_image"] = f"http://{server_ip}:8000{updated_user['profile_image']}"
            
        return JSONResponse({
            "message": "Profile updated successfully", 
            "user": updated_user
        }, status_code=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"message": "Internal server error", "error": str(e)}, status_code=500)





# ----------------- USERS -----------------
@app.get("/users")
async def get_users(id: str = None):
    try:
        if id:
            user = user_collection.find_one({"_id": id})
            if user:
                user["_id"] = str(user["_id"])
                # Return full URL for profile image
                if user.get("profile_image") and user["profile_image"].startswith("/"):
                    server_ip = "192.168.56.219"
                    user["profile_image"] = f"http://{server_ip}:8000{user['profile_image']}"
                return JSONResponse({"user": user}, status_code=200)
            return JSONResponse({"message": "User not found"}, status_code=404)

        # Fetch all users
        # limit=100 is a safe default to prevent massive loads, can be adjusted or removed for small apps
        cursor = user_collection.find({})
        users = []
        for user in cursor:
            # Remove sensitive fields
            user.pop("password", None)
            user.pop("pin_hash", None)
            user["_id"] = str(user["_id"])
            
            # Return full URL for profile image
            if user.get("profile_image") and user["profile_image"].startswith("/"):
                server_ip = "192.168.56.219"
                user["profile_image"] = f"http://{server_ip}:8000{user['profile_image']}"
                
            users.append(user)

        return JSONResponse({"users": users}, status_code=200)

    except Exception as e:
        print(f"Error fetching users: {e}")
        return JSONResponse({"message": "Error fetching users", "error": str(e)}, status_code=500)


@app.post("/messages/send")
async def send_message(message: Message):
    try:
        msg_data = dict(message)
        msg_data["timestamp"] = datetime.utcnow().isoformat()
        msg_data["read"] = False
        
        result = message_collection.insert_one(msg_data)
        
        return JSONResponse({
            "message": "Message sent successfully", 
            "message_id": str(result.inserted_id)
        }, status_code=201)
    except Exception as e:
        print(f"Error sending message: {e}")
        return JSONResponse({"message": "Failed to send message", "error": str(e)}, status_code=500)


@app.post("/messages/read")
async def mark_as_read(data: dict):
    try:
        if "sender_id" not in data or "receiver_id" not in data:
             return JSONResponse({"message": "Missing sender_id or receiver_id"}, status_code=400)

        # Update all messages from sender to receiver that are unread
        result = message_collection.update_many(
            filter={
                "sender_id": data["sender_id"],
                "receiver_id": data["receiver_id"],
                "read": False
            },
            update={"$set": {"read": True}}
        )
        
        return JSONResponse({
            "message": "Messages marked as read", 
            "modified_count": result.update_info.get('modified_count', 0)
        }, status_code=200)
    except Exception as e:
        print(f"Error marking messages as read: {e}")
        return JSONResponse({"message": "Failed to update messages", "error": str(e)}, status_code=500)


@app.get("/messages/conversation")
async def get_conversation(user1_id: str, user2_id: str):
    try:
        # Complex OR query to get messages between two users
        query = {
            "$or": [
                {"sender_id": user1_id, "receiver_id": user2_id},
                {"sender_id": user2_id, "receiver_id": user1_id}
            ]
        }
        
        # Sort by timestamp ascending
        cursor = message_collection.find(query, sort={"timestamp": 1})
        
        messages = []
        for msg in cursor:
            msg["_id"] = str(msg["_id"])
            messages.append(msg)

        return JSONResponse({"messages": messages}, status_code=200)
    except Exception as e:
        print(f"Error fetching conversation: {e}")
        return JSONResponse({"message": "Failed to fetch conversation", "error": str(e)}, status_code=500)


@app.delete("/delete")
async def delete_user(Email: str):
    email = Email.strip().lower() # normalize email
    user_collection.delete_many({"Email": email})
    return JSONResponse(
        content={"message": "User deleted successfully"},
        status_code=status.HTTP_200_OK
    )


@app.post("/active")
async def user_active(Email: str):

    clean_email = Email.strip().lower()

    user = user_collection.find_one(
        {"Email": clean_email}
    )

    if user:
        user_collection.find_one_and_update(
            {"Email": clean_email},
            {
                "$set": {
                    "active": True,
                    "last_seen": datetime.utcnow()
                }
            }
        )

        return JSONResponse(
            content={"message": "User activated successfully"},
            status_code=status.HTTP_200_OK
        )

    return JSONResponse(
        content={"message": "User not on the App"},
        status_code=status.HTTP_404_NOT_FOUND
    ) 
    
