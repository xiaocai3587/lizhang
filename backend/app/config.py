"""应用配置"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "礼账 Lizhang"
    database_url: str = "sqlite:///./data/lizhang.db"
    csv_dir: Path = Path("./data/csv")
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

Path("./data").mkdir(exist_ok=True)
settings.csv_dir.mkdir(parents=True, exist_ok=True)
