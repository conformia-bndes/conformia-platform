"""Tests for personal API key hashing (PBKDF2) and principal resolution."""

import importlib.util
from pathlib import Path

import pytest

from app.core.config import ApiUser, settings
from app.core.security import API_KEY_HASH_ITERATIONS, hash_api_key, resolve_principal

SECRET_ANA = "segredo-da-ana"
SECRET_BIA = "segredo-da-bia"


@pytest.fixture(autouse=True)
def api_users(monkeypatch):
    monkeypatch.setattr(
        settings,
        "API_USERS",
        [
            ApiUser(user_id="ana", role="ANALISTA", key_hash=hash_api_key(SECRET_ANA)),
            ApiUser(user_id="bia", role="AUDITOR", key_hash=hash_api_key(SECRET_BIA)),
        ],
    )


def test_hash_uses_pbkdf2_with_random_salt():
    first, second = hash_api_key("mesmo-segredo"), hash_api_key("mesmo-segredo")
    algorithm, iterations, salt, digest = first.split("$")
    assert algorithm == "pbkdf2_sha256"
    assert int(iterations) == API_KEY_HASH_ITERATIONS
    assert len(salt) == 32 and len(digest) == 64
    assert first != second  # sal aleatorio: mesmo segredo, hashes diferentes


def test_valid_key_resolves_user_and_role():
    principal = resolve_principal(f"ana:{SECRET_ANA}")
    assert (principal.user_id, principal.role) == ("ana", "ANALISTA")


@pytest.mark.parametrize(
    "token",
    [
        "ana:segredo-errado",
        f"bia:{SECRET_ANA}",  # segredo de outro usuario
        f"desconhecido:{SECRET_ANA}",
        SECRET_ANA,  # sem prefixo de usuario
        "ana:",
        "",
        None,
    ],
)
def test_invalid_keys_do_not_resolve(token):
    assert resolve_principal(token) is None


def test_create_api_user_script_output_authenticates(monkeypatch):
    """O script (somente biblioteca padrao) gera chaves no formato aceito pelo servidor."""
    path = Path(__file__).resolve().parents[1] / "scripts" / "create_api_user.py"
    spec = importlib.util.spec_from_file_location("create_api_user", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    key, entry = module.build_api_user("carla.souza", "ANALISTA")
    monkeypatch.setattr(settings, "API_USERS", [ApiUser(**entry)])

    principal = resolve_principal(key)
    assert key.startswith("carla.souza:")
    assert (principal.user_id, principal.role) == ("carla.souza", "ANALISTA")
