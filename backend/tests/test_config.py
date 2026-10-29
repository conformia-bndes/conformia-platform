"""Tests for secrets handling in settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID = {
    "SECRET_KEY": "s",
    "API_KEY": "k",
    "POSTGRES_PASSWORD": "p",
    "MINIO_ROOT_USER": "u",
    "MINIO_ROOT_PASSWORD": "mp",
}


def test_settings_accepts_explicit_secrets(monkeypatch):
    # O CI define DATABASE_URL no ambiente; aqui a URL deve ser montada a partir dos campos.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    cfg = Settings(_env_file=None, **VALID)
    assert cfg.DATABASE_URL.startswith("postgresql+psycopg2://conformia_user:p@")


@pytest.mark.parametrize(
    "url, expected",
    [
        ("postgresql://u:p@db:5432/x", "postgresql+psycopg2://u:p@db:5432/x"),
        ("postgres://u:p@db:5432/x", "postgresql+psycopg2://u:p@db:5432/x"),
        ("postgresql+psycopg2://u:p@db:5432/x", "postgresql+psycopg2://u:p@db:5432/x"),
        ("sqlite:///:memory:", "sqlite:///:memory:"),
    ],
)
def test_database_url_pins_installed_postgres_driver(url, expected):
    """SQLAlchemy 2.1 usa psycopg 3 por padrao em postgresql://; o projeto instala psycopg2."""
    assert Settings(_env_file=None, DATABASE_URL=url, **VALID).DATABASE_URL == expected


def test_settings_rejects_placeholder_secret():
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, **{**VALID, "POSTGRES_PASSWORD": "CHANGE_ME"})
    assert "POSTGRES_PASSWORD" in str(exc.value)


def test_settings_requires_secrets_without_defaults(monkeypatch):
    for name in VALID:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def _settings_with_users(monkeypatch, raw):
    from app.core.config import Settings

    monkeypatch.setenv("API_USERS", raw)
    return Settings()


def test_api_users_parses_json_and_empty_values(monkeypatch):
    digest = "a" * 64
    settings = _settings_with_users(
        monkeypatch, f'[{{"user_id": "ana.silva", "role": "ANALISTA", "key_sha256": "{digest}"}}]'
    )
    assert settings.API_USERS[0].user_id == "ana.silva"
    assert _settings_with_users(monkeypatch, "").API_USERS == []
    assert _settings_with_users(monkeypatch, "[]").API_USERS == []


@pytest.mark.parametrize(
    "raw",
    [
        '[{"user_id": "ana", "role": "ANALISTA", "key_sha256": "nao-e-hash"}]',
        '[{"user_id": "ana", "role": "GERENTE", "key_sha256": "' + "a" * 64 + '"}]',
        '[{"user_id": "ana", "role": "ANALISTA", "key_sha256": "' + "a" * 64 + '"},'
        ' {"user_id": "bia", "role": "ANALISTA", "key_sha256": "' + "a" * 64 + '"}]',
        '[{"user_id": "ana", "role": "ANALISTA", "key_sha256": "' + "a" * 64 + '"},'
        ' {"user_id": "ana", "role": "AUDITOR", "key_sha256": "' + "b" * 64 + '"}]',
    ],
)
def test_api_users_rejects_invalid_configuration(monkeypatch, raw):
    with pytest.raises(ValueError):
        _settings_with_users(monkeypatch, raw)
