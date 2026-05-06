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
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
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


config = Config()
