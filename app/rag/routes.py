from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from groq import Groq
import json
import logging
from datetime import datetime

from app.database.connection import get_db
from app.database.schemas import ConversationDB
from app.auth.routes import get_current_user
from app.auth.models import UserPublic
from app.rag.models import ALLOWED_MODELS, Message
from app.rag.rag_processor import build_context_from_files, web_search
from app.config import settings

router = APIRouter(tags=["RAG Chat"])
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant. Use the provided context if relevant. If web search is enabled and you need up-to-date information, use the web_search tool. Reason step-by-step before deciding to use tools."""

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web using DuckDuckGo for up-to-date information.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
    },
}

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    conv = ConversationDB(user_id=current_user.username)
    result = await db.conversations.insert_one(conv.dict(exclude={"id"}))
    conv.id = str(result.inserted_id)
    return {"conversation_id": conv.id}

@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        oid = ObjectId(conv_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    conv = await db.conversations.find_one({"_id": oid, "user_id": current_user.username})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv["id"] = str(conv["_id"])
    del conv["_id"]
    return conv

@router.post("/conversations/{conv_id}/messages")
async def send_message(
    conv_id: str,
    model: str = Form(...),
    enable_web_search: bool = Form(False),
    message: str = Form(...),
    files: List[UploadFile] = None,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model")
    try:
        oid = ObjectId(conv_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    conv = await db.conversations.find_one({"_id": oid, "user_id": current_user.username})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Load messages
    messages = [Message(**m) for m in conv.get("messages", [])]

    # Build RAG context if files
    rag_context = ""
    if files:
        rag_context = build_context_from_files(files, message)
    
    # System prompt with context
    system_msg = {"role": "system", "content": SYSTEM_PROMPT + (f"\n\nContext: {rag_context}" if rag_context else "")}

    # Append user message
    user_msg = Message(role="user", content=message)
    messages.append(user_msg)

    # Groq client
    client = Groq(api_key=settings.groq_api_key)

    # Tools if enabled
    tools = [WEB_SEARCH_TOOL] if enable_web_search else None

    # Tool loop for reasoning and multiple calls (up to 3 iterations)
    chat_history = [
        system_msg if isinstance(system_msg, dict) else system_msg.dict()
    ] + [
            m if isinstance(m, dict) else m.dict() for m in messages
            ]
    max_tool_loops = 3
    for _ in range(max_tool_loops):
        completion = client.chat.completions.create(
            model=model,
            messages=chat_history,
            temperature=1,
            max_tokens=8192,
            top_p=1,
            stream=False,
            stop=None,
            tools=tools,
        )
        choice = completion.choices[0].message
        if not choice.tool_calls:
            # No more tools, prepare to stream
            break
        for tool_call in choice.tool_calls:
            if tool_call.function.name == "web_search":
                args = json.loads(tool_call.function.arguments)
                query = args["query"]
                result = web_search(query)
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "web_search",
                    "content": result,
                }
                chat_history.append(tool_response)
    else:
        logger.warning("Max tool loops reached")
        raise HTTPException(status_code=500, detail="Too many tool calls")

    # Final streaming call
    completion = client.chat.completions.create(
        model=model,
        messages=chat_history,
        temperature=1,
        max_tokens=8192,
        top_p=1,
        stream=True,
        stop=None,
    )

    # Stream response
    async def generate():
        response_content = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            response_content += content
            yield content
        # Save to DB
        messages.append(Message(role="assistant", content=response_content))
        await db.conversations.update_one(
            {"_id": oid},
            {"$set": {"messages": [m.dict() for m in messages], "updated_at": datetime.utcnow()}}
        )

    return StreamingResponse(generate(), media_type="text/event-stream")