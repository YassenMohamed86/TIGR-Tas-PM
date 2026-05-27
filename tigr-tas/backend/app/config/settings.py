from functools import lru_cache
from typing import Literal
from pathlib import Path
from pydantic import computed_field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    app_version: str
    app_env: Literal["development", "testing", "production"]
    debug: bool
    log_level: str
    host: str
    port: int

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    redis_host: str
    redis_port: int
    redis_db: int = 0
    redis_password: SecretStr
    redis_max_connections: int = 20
    cache_ttl_seconds: int = 3600

    celery_broker_url: str = ""
    celery_result_backend: str = ""
    celery_max_retries: int = 3
    celery_task_timeout: int = 3600

    upload_dir: Path
    max_upload_size_mb: int = 500
    allowed_extensions_str: str = "" # To be mapped, wait pydantic can parse list from string if comma separated.
    # Actually I will use a generic list, pydantic handles comma separated string automatically for list
    allowed_extensions: list[str] = []

    cors_origins: list[str] = []
    cors_allow_credentials: bool = True

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @computed_field
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password.get_secret_value()}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password.get_secret_value()}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
