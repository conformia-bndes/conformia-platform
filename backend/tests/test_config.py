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


def _find_bash():
    import os
    import shutil
    import subprocess
    from pathlib import Path

    candidates = []
    which_bash = shutil.which("bash")
    if which_bash and "system32" not in which_bash.lower():
        candidates.append(which_bash)
    git_bin = shutil.which("git")
    if git_bin:
        git_root = Path(git_bin).resolve().parents[1]
        for rel in ("bin/bash.exe", "usr/bin/bash.exe", "bin/bash"):
            candidate = git_root / rel
            if candidate.exists():
                candidates.append(str(candidate))
    if which_bash:
        candidates.append(which_bash)
    for bash in candidates:
        try:
            res = subprocess.run(
                [bash, "-c", "echo ok"],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, "MSYS_NO_PATHCONV": "1"},
            )
            if res.returncode == 0 and "ok" in res.stdout:
                return bash
        except Exception:
            continue
    return None


def test_setup_env_detects_missing_variables_and_syncs_preserving_secrets(tmp_path):
    """Issue #101: falha listando variaveis ausentes do .env e acrescenta so as novas com --sync."""
    import shutil
    import subprocess
    from pathlib import Path

    bash = _find_bash()
    if not bash:
        pytest.skip("bash indisponivel no ambiente de teste")

    repo_root = Path(__file__).resolve().parents[2]
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    script_copy = scripts_dir / "setup-env.sh"
    shutil.copy2(repo_root / "scripts" / "setup-env.sh", script_copy)
    shutil.copy2(repo_root / ".env.example", tmp_path / ".env.example")

    def run_setup(*args):
        return subprocess.run(
            [bash, str(script_copy), *args],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=15,
        )

    # 1) Gera .env inicial e valida que todas as chaves estao presentes sem CHANGE_ME.
    created = run_setup()
    assert created.returncode == 0, created.stderr
    env_file = tmp_path / ".env"
    initial_lines = env_file.read_text(encoding="utf-8").splitlines()
    assert not any("CHANGE_ME" in line for line in initial_lines if not line.startswith("#"))

    # Segunda execucao sem mudancas e idempotente.
    up_to_date = run_setup()
    assert up_to_date.returncode == 0

    # 2) Simula .env antigo removendo API_KEY e API_USERS, mas guardando SECRET_KEY existente.
    secret_line = next(line for line in initial_lines if line.startswith("SECRET_KEY="))
    outdated_lines = [
        line
        for line in initial_lines
        if not line.startswith("API_KEY=") and not line.startswith("API_USERS=")
    ]
    env_file.write_text("\n".join(outdated_lines) + "\n", encoding="utf-8")

    failed = run_setup()
    assert failed.returncode == 1
    assert "API_KEY" in failed.stderr
    assert "API_USERS" in failed.stderr
    assert "--sync" in failed.stderr

    # 3) --sync acrescenta apenas as chaves novas sem apagar os segredos atuais.
    synced = run_setup("--sync")
    assert synced.returncode == 0, synced.stderr
    assert "API_KEY" in synced.stdout
    assert "API_USERS" in synced.stdout

    final_lines = env_file.read_text(encoding="utf-8").splitlines()
    assert secret_line in final_lines
    api_key_line = next(line for line in final_lines if line.startswith("API_KEY="))
    assert "CHANGE_ME" not in api_key_line
    assert len(api_key_line.split("=", 1)[1]) == 32
    assert "API_USERS=[]" in final_lines

    # Apos o --sync, a validacao padrao volta a passar com codigo 0.
    after_sync = run_setup()
    assert after_sync.returncode == 0
