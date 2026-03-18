from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database.connection import get_db
from app.auth.models import UserCreate, UserPublic, Token
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserPublic:
    try:
        username = verify_access_token(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserPublic(**user)

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    username = user.username.strip().lower()
    email = user.email.lower()
    if await db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        raise HTTPException(status_code=400, detail="Username or email already exists")
    hashed = pwd_context.hash(user.password)
    doc = {
        "username": username,
        "email": email,
        "company": user.company,
        "hashed_password": hashed,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(doc)
    return UserPublic(**doc)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    username = form_data.username.strip().lower()
    user = await db.users.find_one({"username": username})
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(username)
    refresh_token = create_refresh_token(username)
    payload = decode_token(refresh_token)
    await db.sessions.insert_one(
        {
            "user_id": username,
            "refresh_token_hash": hash_refresh_token(refresh_token),
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            "revoked_at": None,
        }
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )

class RefreshIn(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_token(payload: RefreshIn, db=Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    username = decoded.get("sub")
    session_doc = await db.sessions.find_one(
        {
            "user_id": username,
            "revoked_at": None,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        },
        sort=[("created_at", -1)],
    )
    if not session_doc or not verify_refresh_token(payload.refresh_token, session_doc["refresh_token_hash"]):
        raise HTTPException(status_code=401, detail="Refresh token not recognized")
    new_access = create_access_token(username)
    new_refresh = create_refresh_token(username)
    await db.sessions.update_one(
        {"_id": session_doc["_id"]}, {"$set": {"revoked_at": datetime.now(timezone.utc)}}
    )
    payload_new = decode_token(new_refresh)
    await db.sessions.insert_one(
        {
            "user_id": username,
            "refresh_token_hash": hash_refresh_token(new_refresh),
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.fromtimestamp(payload_new["exp"], tz=timezone.utc),
            "revoked_at": None,
        }
    )
    return Token(access_token=new_access, refresh_token=new_refresh, expires_in=settings.access_token_expire_minutes * 60)

@router.post("/logout")
async def logout(payload: RefreshIn, db=Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        return {"ok": True}
    username = decoded.get("sub")
    session_doc = await db.sessions.find_one(
        {
            "user_id": username,
            "revoked_at": None,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        },
        sort=[("created_at", -1)],
    )
    if not session_doc:
        return {"ok": True}
    if verify_refresh_token(payload.refresh_token, session_doc["refresh_token_hash"]):
        await db.sessions.update_one(
            {"_id": session_doc["_id"]}, {"$set": {"revoked_at": datetime.now(timezone.utc)}}
        )
    return {"ok": True}

@router.get("/profile", response_model=UserPublic)
async def read_users_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user