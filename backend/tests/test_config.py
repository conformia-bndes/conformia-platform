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
    # O CI define DATABASE_URL e POSTGRES_* no ambiente; aqui a URL deve ser montada a partir
    # dos padroes e do segredo informado.
    for name in (
        "DATABASE_URL",
        "POSTGRES_SERVER",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_DB",
    ):
        monkeypatch.delenv(name, raising=False)
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


SECURITY_VARS = ("ENVIRONMENT", "DEBUG", "ALLOW_ANONYMOUS_ACCESS")


@pytest.fixture
def clean_security_env(monkeypatch):
    """O conftest fixa ENVIRONMENT=test; estes testes precisam enxergar os padroes do codigo."""
    for name in SECURITY_VARS:
        monkeypatch.delenv(name, raising=False)


def test_security_defaults_are_production_without_debug_or_anonymous(clean_security_env):
    cfg = Settings(_env_file=None, **VALID)
    assert cfg.ENVIRONMENT == "production"
    assert cfg.DEBUG is False
    assert cfg.ALLOW_ANONYMOUS_ACCESS is False


def test_anonymous_access_requires_explicit_opt_in(clean_security_env):
    cfg = Settings(_env_file=None, ENVIRONMENT="development", ALLOW_ANONYMOUS_ACCESS=True, **VALID)
    assert cfg.ALLOW_ANONYMOUS_ACCESS is True
    # Mudar so o ambiente nao liga o acesso anonimo.
    assert (
        Settings(_env_file=None, ENVIRONMENT="development", **VALID).ALLOW_ANONYMOUS_ACCESS is False
    )


def test_production_rejects_anonymous_access(clean_security_env):
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, ENVIRONMENT="production", ALLOW_ANONYMOUS_ACCESS=True, **VALID)
    assert "ALLOW_ANONYMOUS_ACCESS" in str(exc.value)


def test_production_rejects_debug(clean_security_env):
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, ENVIRONMENT="production", DEBUG=True, **VALID)
    assert "DEBUG" in str(exc.value)


def test_debug_is_allowed_outside_production(clean_security_env):
    assert Settings(_env_file=None, ENVIRONMENT="development", DEBUG=True, **VALID).DEBUG is True


@pytest.mark.parametrize("value", ["prod", "staging", "Production", ""])
def test_unknown_environment_is_rejected(clean_security_env, value):
    """Um erro de digitacao nao pode virar um ambiente sem as protecoes de producao."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT=value, **VALID)


def test_env_example_is_the_explicit_local_opt_in():
    """O modelo do .env e o opt-in local; o padrao do codigo continua seguro."""
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")
    lines = {line.strip() for line in text.splitlines()}
    assert "ENVIRONMENT=development" in lines
    assert "ALLOW_ANONYMOUS_ACCESS=true" in lines


VALID_HASH = "pbkdf2_sha256$200000$" + "a" * 32 + "$" + "b" * 64
OTHER_HASH = "pbkdf2_sha256$200000$" + "c" * 32 + "$" + "d" * 64
WEAK_HASH = "pbkdf2_sha256$099999$" + "a" * 32 + "$" + "b" * 64


def _settings_with_users(monkeypatch, raw):
    from app.core.config import Settings

    monkeypatch.setenv("API_USERS", raw)
    return Settings()


def test_api_users_parses_json_and_empty_values(monkeypatch):
    settings = _settings_with_users(
        monkeypatch, f'[{{"user_id": "ana.silva", "role": "ANALISTA", "key_hash": "{VALID_HASH}"}}]'
    )
    assert settings.API_USERS[0].user_id == "ana.silva"
    assert _settings_with_users(monkeypatch, "").API_USERS == []
    assert _settings_with_users(monkeypatch, "[]").API_USERS == []


@pytest.mark.parametrize(
    "raw",
    [
        # hash SHA-256 simples (formato anterior) nao e aceito
        '[{"user_id": "ana", "role": "ANALISTA", "key_hash": "' + "a" * 64 + '"}]',
        # iteracoes abaixo do minimo
        '[{"user_id": "ana", "role": "ANALISTA", "key_hash": "' + WEAK_HASH + '"}]',
        '[{"user_id": "ana", "role": "GERENTE", "key_hash": "' + VALID_HASH + '"}]',
        '[{"user_id": "ana", "role": "ANALISTA", "key_hash": "' + VALID_HASH + '"},'
        ' {"user_id": "bia", "role": "ANALISTA", "key_hash": "' + VALID_HASH + '"}]',
        '[{"user_id": "ana", "role": "ANALISTA", "key_hash": "' + VALID_HASH + '"},'
        ' {"user_id": "ana", "role": "AUDITOR", "key_hash": "' + OTHER_HASH + '"}]',
    ],
)
def test_api_users_rejects_invalid_configuration(monkeypatch, raw):
    with pytest.raises(ValueError):
        _settings_with_users(monkeypatch, raw)
