from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime

ALLOWED_MODELS = [
    "allam-2-7b",  # Fixed typo from "allam-2-7b"
    "groq/compound",
    "groq/compound-mini",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",  # Assuming typo from "llama-3.3-70b-versatile"
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-guard-4-12b",
    "meta-llama/llama-prompt-guard-2-22m",
    "meta-llama/llama-prompt-guard-2-86m",
    "moonshotai/kimi-k2-instruct",
    "moonshotai/kimi-k2-instruct-0905",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3-32b",
]

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    id: Optional[str] = None  # str(ObjectId)
    user_id: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    model: str = Field(..., description="Groq model", enum=ALLOWED_MODELS)
    enable_web_search: bool = False
    message: str = Field(..., min_length=1)