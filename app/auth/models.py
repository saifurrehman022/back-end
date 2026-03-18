from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="User email (must be unique)")
    company: str = Field(default="", max_length=128)
    password: str = Field(..., min_length=8, description="User password (will be hashed).")

class UserInDB(BaseModel):
    username: str
    email: str
    company: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPublic(BaseModel):
    username: str
    email: str
    company: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int