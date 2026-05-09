import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "life-os-dev-secret")
    LIFE_OS_ADMIN_PASSWORD = os.getenv("LIFE_OS_ADMIN_PASSWORD", "").strip()
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    PLUGGY_CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID", "").strip()
    PLUGGY_CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET", "").strip()
    PLUGGY_WEBHOOK_SECRET = os.getenv("PLUGGY_WEBHOOK_SECRET", "").strip()
    PLUGGY_API_BASE_URL = os.getenv("PLUGGY_API_BASE_URL", "https://api.pluggy.ai").rstrip("/")
    PORT = int(os.getenv("PORT", "5000"))
    LIFE_OS_SAMPLE_SECONDS = int(os.getenv("LIFE_OS_SAMPLE_SECONDS", "5"))
    LIFE_OS_DISABLE_TRACKER = os.getenv("LIFE_OS_DISABLE_TRACKER", "").lower() in {
        "1",
        "true",
        "yes",
    }
    LIFE_OS_ENABLE_WINDOWS_TRACKER = os.getenv(
        "LIFE_OS_ENABLE_WINDOWS_TRACKER",
        "true" if os.name == "nt" else "false",
    ).lower() in {"1", "true", "yes"}

    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'life_os.db'}",
    )

    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() in {
        "1",
        "true",
        "yes",
    }


config = Config()
