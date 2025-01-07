from pydantic import BaseSettings
from typing import List, Optional
import urllib.parse


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "CR8 Platform"

    # Database configuration
    DATABASE_URL: str
    SUPABASE_ANON_KEY: str
    DB_user: str
    DB_password: str
    DB_host: str
    DB_port: int
    DB_name: str

    # WebSocket settings
    WS_HOST: str
    WS_PORT: int

    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]

    # Logto authentication
    # LOGTO_ENDPOINT: str
    # LOGTO_APP_ID: str
    # LOGTO_CLIENT_SECRET: str

    # Minio Config
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.DB_user}:{urllib.parse.quote_plus(self.DB_password)}@{self.DB_host}:{self.DB_port}/{self.DB_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
