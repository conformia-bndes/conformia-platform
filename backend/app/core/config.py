"""Application configuration module using pydantic-settings."""

import json
from functools import lru_cache
from typing import Annotated, List, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

UserRole = Literal["ANALISTA", "AUDITOR", "ADMIN"]


class ApiUser(BaseModel):
    """
    Usuario identificado por chave de API pessoal. Somente o hash SHA-256 da chave e
    configurado; a chave em si fica com o usuario (gerada por scripts/create_api_user.py).
    """

    user_id: str = Field(pattern=r"^[a-z0-9._-]{3,64}$")
    role: UserRole
    key_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def _with_explicit_postgres_driver(url: str) -> str:
    """
    Fixa o driver psycopg2 (o instalado pelo projeto) em URLs PostgreSQL sem driver.
    A partir do SQLAlchemy 2.1, "postgresql://" passa a usar o psycopg 3 por padrao, que
    nao e dependencia do backend; a URL explicita independe da versao do SQLAlchemy.
    """
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            return "postgresql+psycopg2://" + url[len(scheme) :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Informações do Projeto
    PROJECT_NAME: str = "Conform.IA BNDES Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    # Segredos: obrigatorios e sem valor default no codigo (definidos via .env / ambiente)
    SECRET_KEY: str
    API_KEY: str
    # Usuarios com chave pessoal (JSON). Necessarios para revisao humana e segregacao.
    API_USERS: Annotated[List[ApiUser], NoDecode] = []

    @field_validator("API_USERS", mode="before")
    @classmethod
    def parse_api_users(cls, v: Union[str, List]) -> List:
        if isinstance(v, str):
            return json.loads(v) if v.strip() else []
        return v

    @field_validator("API_USERS")
    @classmethod
    def reject_duplicate_api_users(cls, users: List[ApiUser]) -> List[ApiUser]:
        if len({u.user_id for u in users}) != len(users):
            raise ValueError("API_USERS contem user_id duplicado.")
        if len({u.key_sha256 for u in users}) != len(users):
            raise ValueError("API_USERS contem a mesma chave para mais de um usuario.")
        return users

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
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
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "conformia_db"
    DATABASE_URL: Union[str, None] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str) and v:
            return _with_explicit_postgres_driver(v)
        # Extrai valores para montar a URL caso DATABASE_URL não seja passada explicitamente
        values = info.data
        user = values.get("POSTGRES_USER", "conformia_user")
        password = values.get("POSTGRES_PASSWORD", "")
        server = values.get("POSTGRES_SERVER", "postgres")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "conformia_db")
        return _with_explicit_postgres_driver(
            f"postgresql://{user}:{password}@{server}:{port}/{db}"
        )

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
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
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

    @model_validator(mode="after")
    def reject_placeholder_secrets(self) -> "Settings":
        """Falha cedo se algum segredo ainda for o placeholder do .env.example."""
        secrets = {
            "SECRET_KEY": self.SECRET_KEY,
            "API_KEY": self.API_KEY,
            "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
            "MINIO_ROOT_USER": self.MINIO_ROOT_USER,
            "MINIO_ROOT_PASSWORD": self.MINIO_ROOT_PASSWORD,
        }
        pending = [name for name, value in secrets.items() if not value or "CHANGE_ME" in value]
        if pending:
            raise ValueError(
                f"Segredos nao configurados: {', '.join(pending)}. "
                "Gere o arquivo .env com 'make env' (ou substitua os CHANGE_ME manualmente)."
            )
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
