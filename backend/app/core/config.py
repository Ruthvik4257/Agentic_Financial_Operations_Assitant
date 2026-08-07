import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Agentic Financial Operations Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/finops.db"

    # AI / LLM Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Telegram Gateway
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_MODE: str = "polling"  # polling or webhook
    TELEGRAM_MANAGER_CHAT_ID: str = ""

    # ERPNext Integration
    ERPNEXT_MODE: str = "mock"  # "mock" for embedded engine or "live" for Frappe REST API
    ERPNEXT_BASE_URL: str = "http://localhost:8000/api/resource"
    ERPNEXT_API_KEY: str = "mock_key"
    ERPNEXT_API_SECRET: str = "mock_secret"

    # Financial Governance Policies
    MAX_AUTO_REFUND_LIMIT: float = 200.00
    MAX_FRAUD_RISK_THRESHOLD: float = 0.30
    MAX_DAILY_REFUND_CAP: float = 5000.00

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
