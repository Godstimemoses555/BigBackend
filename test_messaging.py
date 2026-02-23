import requests
import time

API_URL = "http://192.168.56.219:8000"

def test_messaging_flow():
    # 1. Create two test users
    user1 = {
        "name": "User One", "age": 25, "Email": "user1@test.com", 
        "password": "password123", "secret_pin": "1234"
    }
    user2 = {
        "name": "User Two", "age": 30, "Email": "user2@test.com", 
        "password": "password123", "secret_pin": "1234"
    }
    
    # Register/Ensure users exist (ignoring errors if they exist)
    requests.post(f"{API_URL}/create", json=user1)
    requests.post(f"{API_URL}/create", json=user2)
    
    # 2. Send message from User1 to User2
    msg_payload = {
        "sender_id": user1["Email"],
        "receiver_id": user2["Email"],
        "content": "Hello from User 1"
    }
    
    print("Sending message...")
    res = requests.post(f"http://192.168.56.219/messages/send", json=msg_payload)
    if res.status_code == 201:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {res.text}")
        return

    # 3. Read conversation as User2
    print("Fetching conversation...")
    res = requests.get(f"http://192.168.56.219/messages/conversation", params={"user1_id": user1["Email"], "user2_id": user2["Email"]})
    
    if res.status_code == 200:
        messages = res.json().get("messages", [])
        if any(m["content"] == "Hello from User 1" for m in messages):
            print("Message verification successful: Message found in conversation.")
        else:
            print("Message verification failed: Message NOT found.")
            print("Messages:", messages)
    else:
        print(f"Failed to fetch conversation: {res.text}")

if __name__ == "__main__":
    test_messaging_flow()
