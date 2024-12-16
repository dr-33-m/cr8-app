from pydantic import BaseSettings, PostgresDsn, validator
from typing import List, Optional


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "CR8 Platform"

    # Database configuration
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: Optional[PostgresDsn]

    # WebSocket settings
    WS_HOST: str
    WS_PORT: int

    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]

    # Logto authentication
    LOGTO_ENDPOINT: str
    LOGTO_APP_ID: str
    # LOGTO_CLIENT_SECRET: str

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                user=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_HOST"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
