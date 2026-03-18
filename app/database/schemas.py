from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# User Schemas (adapted)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="User email (must be unique)")
    company: str = Field(default="", max_length=128)
    password: str = Field(..., min_length=8, description="User password (will be hashed).")

class UserDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    password_hash: str = Field(alias="hashed_password")
    company: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    roles: List[str] = Field(default_factory=lambda: ["user"])

class SessionDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    refresh_token_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

# Conversation Schemas
class Message(BaseModel):
    role: str
    content: str

class ConversationDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    meta: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"model": "llama-3.1-8b-instant"}

# Audit Log (optional, for security)
class AuditLogDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    action: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: Dict[str, Any] = Field(default_factory=dict)

# MongoDB Indexes for Performance
MONGO_INDEXES = {
    "users": [
        {"keys": [("username", 1)], "unique": True},
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("created_at", -1)]},
    ],
    "sessions": [
        {"keys": [("user_id", 1), ("created_at", -1)]},
        {"keys": [("expires_at", 1)]},
    ],
    "conversations": [
        {"keys": [("user_id", 1), ("created_at", -1)]},
    ],
    "audit_logs": [
        {"keys": [("user_id", 1), ("created_at", -1)]},
        {"keys": [("action", 1), ("created_at", -1)]},
    ],
}