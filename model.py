from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ---------------- Models ----------------
class User(BaseModel):
    age: int
    name: str
    Email: EmailStr
    message: List[str] = []
    friends: List[str] = []
    gender: Optional[str] = None
    is_active: Optional[bool] = False
    profile_image: Optional[str] = None
    password: str

class CreateSecretPin(BaseModel):
    Email: EmailStr
    secretpin: str

class Login(BaseModel):
    Email: EmailStr
    secretpin: str

class Message(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    timestamp: Optional[str] = None
    read: bool = False