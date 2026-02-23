import requests
import json

url = "http://127.0.0.1:8000/create"
# Note: User's backend is likely running on 8000. 
# The frontend uses 192.168.56.219 (VirtualBox Host-Only Adapter?). 
# From the agent environment, we should try localhost if the server is running locally.
# However, I need to know if the server IS running.
# I will try to run the server in the background if I can't connect.
# But for now let's assume I can start a server instance or connect to one.

# Payload from Register.js
payload = {
    "name": "Test User",
    "age": 25,
    "Email": "test_register@example.com",
    "password": "password123",
    "secret_pin": "1234",  # Extra field sent by frontend
    "gender": "male",
    "message": [],
    "friends": [],
    "is_active": False
}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload, timeout=5)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    
    try:
        data = response.json()
        print("Response JSON:", json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("Response Text (Not JSON):", response.text)

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
