import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Family AI Butler"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev_secret_key"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_GROUP_ID: str = ""
    USER_TELEGRAM_ID: str = ""
    PARTNER_TELEGRAM_ID: str = ""
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # AI Keys
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://family_user:family_password@postgres:5432/family_db"
    SYNC_DATABASE_URL: str = "postgresql://family_user:family_password@postgres:5432/family_db"

    # Redis & Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
