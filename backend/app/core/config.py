"""Application configuration module using pydantic-settings."""

from functools import lru_cache
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Informações do Projeto
    PROJECT_NAME: str = "Conform.IA BNDES Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "conformia_default_secret_key_change_in_production_12345"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Banco de Dados PostgreSQL
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "conformia_user"
    POSTGRES_PASSWORD: str = "conformia_secret_pass"
    POSTGRES_DB: str = "conformia_db"
    DATABASE_URL: Union[str, None] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str) and v:
            return v
        # Extrai valores para montar a URL caso DATABASE_URL não seja passada explicitamente
        values = info.data
        user = values.get("POSTGRES_USER", "conformia_user")
        password = values.get("POSTGRES_PASSWORD", "conformia_secret_pass")
        server = values.get("POSTGRES_SERVER", "postgres")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "conformia_db")
        return f"postgresql://{user}:{password}@{server}:{port}/{db}"

    # Cache e Filas - Redis & Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: Union[str, None] = None
    CELERY_RESULT_BACKEND: Union[str, None] = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_broker_url(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str) and v:
            return v
        return info.data.get("REDIS_URL", "redis://redis:6379/0")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_backend_url(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str) and v:
            return v
        return info.data.get("REDIS_URL", "redis://redis:6379/0")

    # Armazenamento de Objetos - MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = "conformia_minio_admin"
    MINIO_ROOT_PASSWORD: str = "conformia_minio_secret"
    MINIO_BUCKET_NAME: str = "documents"
    MINIO_USE_SSL: bool = False

    # Motor de Regras e IDP
    RULES_PATH: str = "/rules/schemas"
    TESSERACT_CMD: Union[str, None] = None

    # IA e Avaliações Semânticas (LLM)
    OPENAI_API_KEY: Union[str, None] = None
    ANTHROPIC_API_KEY: Union[str, None] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
