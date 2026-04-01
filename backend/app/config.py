from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    steam_api_key: str = ""

    # Database
    database_url: str = "sqlite:///./data/gametopia.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # CORS
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure data directory exists
Path("./data").mkdir(exist_ok=True)
