"""Tests for container resource limits, configurable concurrency and production compose (#103)."""

from pathlib import Path
import yaml

from app.core.celery_app import celery
from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel_path: str) -> dict:
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    # Remove a tag customizada !reset do Docker Compose para parsear com PyYAML padrao.
    cleaned = text.replace("!reset", "")
    return yaml.safe_load(cleaned)


def test_docker_compose_defines_resource_limits_for_backend_worker_and_frontend():
    compose = _load_yaml("infra/docker-compose.yml")
    services = compose["services"]

    for name in ("backend", "worker", "frontend"):
        limits = services[name].get("deploy", {}).get("resources", {}).get("limits", {})
        assert "cpus" in limits, f"{name} sem deploy.resources.limits.cpus"
        assert "memory" in limits, f"{name} sem deploy.resources.limits.memory"


def test_celery_concurrency_is_configurable_in_compose_and_settings():
    compose = _load_yaml("infra/docker-compose.yml")
    worker_cmd = " ".join(compose["services"]["worker"]["command"])
    assert "--concurrency=${CELERY_CONCURRENCY:-2}" in worker_cmd

    cfg = Settings(
        _env_file=None,
        SECRET_KEY="s",
        API_KEY="k",
        POSTGRES_PASSWORD="p",
        MINIO_ROOT_USER="u",
        MINIO_ROOT_PASSWORD="mp",
        WEB_CONCURRENCY=4,
        CELERY_CONCURRENCY=3,
    )
    assert cfg.WEB_CONCURRENCY == 4
    assert cfg.CELERY_CONCURRENCY == 3
    assert celery.conf.worker_concurrency >= 1


def test_production_compose_profile_runs_without_reload_and_exposes_8080():
    prod = _load_yaml("infra/docker-compose.prod.yml")
    services = prod["services"]

    backend_cmd = services["backend"]["command"]
    assert "--reload" not in backend_cmd
    backend_env = services["backend"]["environment"]
    assert "WEB_CONCURRENCY" in backend_env
    assert "DB_POOL_SIZE" in backend_env
    assert "DB_MAX_OVERFLOW" in backend_env

    frontend = services["frontend"]
    assert frontend["build"]["target"] == "production"
    assert any("8080" in str(p) for p in frontend["ports"])


def test_soak_test_assets_exist_and_default_to_30_minutes():
    soak_js = (REPO_ROOT / "tests" / "load" / "soak.js").read_text(encoding="utf-8")
    soak_sh = (REPO_ROOT / "scripts" / "soak_test.sh").read_text(encoding="utf-8")
    assert '"30m"' in soak_js
    assert "pg_stat_activity" in soak_sh
    assert "docker stats" in soak_sh
