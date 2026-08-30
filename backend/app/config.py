import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Database & Storage
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./recruiter_ai.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    # Security & Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-recruiterai-production-key-change-me-1234567890")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours default
    CORS_ORIGINS: List[str] = ["*"]

    # AI & LLM Providers
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")  # groq, openai, anthropic, ollama, mock
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # External Integrations Mode
    USE_MOCK_APIS: bool = os.getenv("USE_MOCK_APIS", "true").lower() in ("true", "1", "yes")

    # Calendar Integration Credentials
    GOOGLE_CALENDAR_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    OUTLOOK_CALENDAR_CREDENTIALS: Optional[str] = os.getenv("OUTLOOK_CALENDAR_CREDENTIALS")

    # Email Service Credentials
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "apikey")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "recruitment@recruiterai.com")

    # Assessment Integrations
    HACKERRANK_API_KEY: Optional[str] = os.getenv("HACKERRANK_API_KEY")
    CODILITY_API_KEY: Optional[str] = os.getenv("CODILITY_API_KEY")
    METTL_API_KEY: Optional[str] = os.getenv("METTL_API_KEY")

    # Background Verification & Reference Checks
    CHECKR_API_KEY: Optional[str] = os.getenv("CHECKR_API_KEY")
    SPRINGVERIFY_API_KEY: Optional[str] = os.getenv("SPRINGVERIFY_API_KEY")

    # ATS & Sourcing Feeds
    GREENHOUSE_API_KEY: Optional[str] = os.getenv("GREENHOUSE_API_KEY")
    LEVER_API_KEY: Optional[str] = os.getenv("LEVER_API_KEY")

settings = Settings()
