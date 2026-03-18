import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = os.getenv("MONGO_URI")
    database_name: str = os.getenv("DATABASE_NAME")
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()