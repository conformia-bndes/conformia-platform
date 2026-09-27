"""SQLAlchemy 2.0 database engine, session factory and session dependency."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Conexão com pool resiliente e pre-ping para evitar conexões mortas
# Para SQLite de teste em memória ou PostgreSQL em runtime
connect_args = {}
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL
    or "postgresql://conformia_user:conformia_secret_pass@postgres:5432/conformia_db",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection para sessões transacionais do SQLAlchemy.
    Garante fechamento correto após a requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
