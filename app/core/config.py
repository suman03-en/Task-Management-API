import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

timezone_nepal = timezone(timedelta(hours=5, minutes=45), name="Asia/Kathmandu")


# returns timezone aware time
def utc_now() -> datetime:
    return datetime.now(timezone_nepal)


@dataclass(frozen=True)
class Settings:
    app_name: str
    debug: bool
    database_url: str


@lru_cache
def get_settings() -> Settings:
    debug_value = os.getenv("DEBUG", "false").strip().lower()
    return Settings(
        app_name=os.getenv("APP_NAME", "Task Management API"),
        debug=debug_value in {"1", "true", "yes", "on"},
        database_url=os.getenv("DATABASE_URL", "sqlite:///./task_management.db"),
    )

if __name__ == "__main__":
    settings = get_settings()
    print(settings)
