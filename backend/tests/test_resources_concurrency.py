"""Tests for container resource limits, concurrency and production compose (#103, #164)."""

from pathlib import Path
import re
import pytest
import yaml

from app.core.celery_app import celery, process_document_task
from app.core.config import Settings
from app.db.models.document import Document

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel_path: str) -> dict:
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    # Remove a tag customizada !reset do Docker Compose para parsear com PyYAML padrao.
    cleaned = text.replace("!reset", "")
    return yaml.safe_load(cleaned)


def _merge_production_compose() -> dict:
    """Calcula o perfil efetivo de producao (docker-compose.yml + docker-compose.prod.yml)."""
    base_text = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    prod_raw = (REPO_ROOT / "infra" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    base = yaml.safe_load(base_text)
    prod = yaml.safe_load(prod_raw.replace("!reset", ""))

    # Identifica quais servicos usam `ports: !reset` no overlay de producao.
    reset_ports_services = set()
    current_service = None
    for line in prod_raw.splitlines():
        m_svc = re.match(r"^  ([a-z0-9_-]+):\s*$", line)
        if m_svc:
            current_service = m_svc.group(1)
        elif current_service and re.match(r"^    ports:\s*!reset", line):
            reset_ports_services.add(current_service)

    merged_services = {}
    for svc_name, svc_cfg in base["services"].items():
        merged = dict(svc_cfg)
        override = prod.get("services", {}).get(svc_name, {})
        for k, v in override.items():
            if k == "ports" and svc_name in reset_ports_services:
                merged["ports"] = list(v or [])
            else:
                merged[k] = v
        merged_services[svc_name] = merged

    return {"services": merged_services}


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


def test_effective_production_profile_does_not_publish_data_service_ports():
    """Issue #164: perfil efetivo de producao nao publica as portas 5432, 6380, 9000 e 9001."""
    effective = _merge_production_compose()
    services = effective["services"]

    for data_service in ("postgres", "redis", "minio"):
        published = services[data_service].get("ports") or []
        assert published == [], f"{data_service} nao deve publicar portas em producao: {published}"

    all_published_ports = [str(p) for svc in services.values() for p in (svc.get("ports") or [])]
    for forbidden_port in ("5432", "6380", "9000", "9001"):
        assert not any(
            forbidden_port in mapping for mapping in all_published_ports
        ), f"Porta {forbidden_port} ainda publicada no perfil de producao: {all_published_ports}"


def test_redis_image_is_pinned_by_digest_and_requires_password():
    """Issue #164: imagem do Redis fixada por digest e autenticada com REDIS_PASSWORD."""
    compose = _load_yaml("infra/docker-compose.yml")
    redis_svc = compose["services"]["redis"]

    image = redis_svc["image"]
    assert re.match(
        r"^redis:7-alpine@sha256:[0-9a-f]{64}$", image
    ), f"Imagem do Redis deve ser fixada por digest SHA-256: {image}"

    cmd = " ".join(redis_svc["command"])
    assert "--requirepass" in cmd
    assert "REDIS_PASSWORD" in cmd

    health_cmd = " ".join(redis_svc["healthcheck"]["test"])
    assert "REDIS_PASSWORD" in health_cmd

    backend_env = compose["x-backend"]["environment"]
    for key in ("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
        assert "REDIS_PASSWORD" in backend_env[key], f"{key} sem REDIS_PASSWORD no compose"
        assert "redis://:" in backend_env[key]

    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    env_lines = {line.strip() for line in env_example.splitlines() if not line.startswith("#")}
    assert "REDIS_PASSWORD=CHANGE_ME" in env_lines


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "../../etc/x",
        "../outside.pdf",
        "/etc/passwd",
        "/tmp/other_dir/doc-1_cnd.pdf",
        "other-doc_cnd.pdf",
        "doc-10_cnd.pdf",  # prefixo de outro document_id nao pode ser aceito
    ],
)
def test_process_document_task_rejects_file_path_outside_upload_dir_without_downloading(
    monkeypatch, tmp_path, unsafe_path
):
    """Issue #164: rejeita file_path fora de UPLOAD_DIR e nao chama download_file."""
    from app.core import storage as storage_module

    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    download_calls = []
    monkeypatch.setattr(
        storage_module.storage_service,
        "download_file",
        lambda object_name, destination_path: download_calls.append(
            (object_name, destination_path)
        ),
    )

    with pytest.raises(ValueError):
        process_document_task.run("doc-1", unsafe_path, object_name="evil/../../etc/passwd")

    assert download_calls == []


def test_process_document_task_derives_object_name_and_ignores_untrusted_broker_arg(
    db_session, monkeypatch, tmp_path
):
    """Issue #164: object_name e file_path sao derivados do documento dentro de UPLOAD_DIR."""
    from app.core import storage as storage_module
    from tests.conftest import TestingSessionLocal
    from tests.synthetic_pdfs import build_native_pdf

    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSessionLocal)

    doc_id = "doc-safe-164"
    safe_filename = f"{doc_id}_cnd.pdf"
    doc = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename="cnd.pdf",
        content_type="application/pdf",
        file_size=128,
        storage_path=f"s3://documents/{safe_filename}",
        status="PROCESSING",
    )
    db_session.add(doc)
    db_session.commit()

    download_calls = []

    def fake_download(object_name: str, destination_path: str):
        download_calls.append((object_name, destination_path))
        Path(destination_path).write_bytes(
            build_native_pdf(
                [
                    [
                        "SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL",
                        "CERTIDAO NEGATIVA DE DEBITOS RELATIVOS AOS TRIBUTOS FEDERAIS "
                        "E A DIVIDA ATIVA DA UNIAO",
                        "CNPJ: 12.345.678/0001-90",
                        "Valida ate: 31/12/2099",
                    ]
                ]
            )
        )

    monkeypatch.setattr(storage_module.storage_service, "download_file", fake_download)

    expected_path = str(tmp_path / safe_filename)
    result = process_document_task.run(
        doc_id,
        expected_path,
        object_name="../../untrusted/object.pdf",
    )

    assert result["status"] == "COMPLETED"
    assert download_calls == [(safe_filename, expected_path)]


def test_soak_test_assets_exist_and_default_to_30_minutes():
    soak_js = (REPO_ROOT / "tests" / "load" / "soak.js").read_text(encoding="utf-8")
    soak_sh = (REPO_ROOT / "scripts" / "soak_test.sh").read_text(encoding="utf-8")
    assert '"30m"' in soak_js
    assert "pg_stat_activity" in soak_sh
    assert "docker stats" in soak_sh
