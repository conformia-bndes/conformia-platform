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
elif settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
    # Falha rapido se o Postgres nao responde (o padrao do driver espera indefinidamente).
    connect_args["connect_timeout"] = 3

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
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
