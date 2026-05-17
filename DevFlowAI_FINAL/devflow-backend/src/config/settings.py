from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "DevFlow AI"
    DEBUG: bool = False
    SECRET_KEY: str

    # Database
    DATABASE_URL: str = "postgresql://devflow:devflow123@localhost:5432/devflow_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5500"

    # IBM watsonx / AI
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    AI_MODEL: str = "meta-llama/llama-3-3-70b-instruct"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # ─── EMAIL (Gmail SMTP) ───
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 465
    EMAIL_USER: str = ""           # your Gmail: nagavalli@gmail.com
    EMAIL_PASSWORD: str = ""       # Gmail App Password (16 chars)
    EMAIL_FROM_NAME: str = "DevFlow AI"
    SEND_WELCOME_EMAIL: bool = True
    SEND_LOGIN_ALERT: bool = False  # set True to alert on every login

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5500",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "null",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate critical secrets in production
        if not self.DEBUG:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be set via environment variables and be at least 32 characters long in production")
            if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be set via environment variables and be at least 32 characters long in production")

settings = Settings()
