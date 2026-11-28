"""Testes para o workflow de CD (cd.yml), gate de CI da tag (#171) e compose GHCR (#102)."""

import importlib.util
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_verify_release_ci():
    path = REPO_ROOT / "scripts" / "verify_release_ci.py"
    spec = importlib.util.spec_from_file_location("verify_release_ci", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cd_workflow_supports_dry_run_and_validates_containers():
    """Garante que o cd.yml suporta workflow_dispatch com push=false e valida os containers."""
    cd_path = REPO_ROOT / ".github" / "workflows" / "cd.yml"
    data = yaml.safe_load(cd_path.read_text(encoding="utf-8"))

    triggers = data.get("on") or data.get(True)
    assert "workflow_dispatch" in triggers
    assert "workflow_call" in triggers

    dispatch_inputs = triggers["workflow_dispatch"]["inputs"]
    assert dispatch_inputs["tag"]["required"] is True
    assert dispatch_inputs["push"]["default"] is False

    deploy_job = data["jobs"]["deploy"]
    matrix_services = {
        item["service"]: item for item in deploy_job["strategy"]["matrix"]["include"]
    }
    assert matrix_services["backend"]["target"] == "runtime"
    assert matrix_services["frontend"]["target"] == "production"

    step_names = [step.get("name", "") for step in deploy_job["steps"]]
    assert any("Carregar imagem para validacao local" in name for name in step_names)
    assert any("Validar container de producao" in name for name in step_names)
    assert any("Validar pull das tags publicadas no GHCR" in name for name in step_names)


def test_compose_ghcr_uses_published_images_and_port_8080():
    """Garante que o compose para imagens GHCR usa ghcr.io e expoe o frontend na porta 8080."""
    compose_ghcr = (REPO_ROOT / "infra" / "docker-compose.ghcr.yml").read_text(encoding="utf-8")

    assert "ghcr.io/conformia-bndes/conformia-platform/backend" in compose_ghcr
    assert "ghcr.io/conformia-bndes/conformia-platform/frontend" in compose_ghcr
    assert "${FRONTEND_PROD_PORT:-8080}:8080" in compose_ghcr
    assert "http://127.0.0.1:8080/" in compose_ghcr
    active_lines = "\n".join(
        line for line in compose_ghcr.splitlines() if not line.lstrip().startswith("#")
    )
    assert "--reload" not in active_lines


def test_backend_dockerfile_embeds_normative_rules():
    """Garante que a imagem runtime do backend inclui /rules para execucao via GHCR."""
    dockerfile = (REPO_ROOT / "infra" / "Dockerfile.backend").read_text(encoding="utf-8")
    assert "COPY --chown=conformia:conformia ./rules /rules" in dockerfile


def test_devops_docs_registers_ghcr_package_visibility_and_compose():
    """Garante que a decisao de visibilidade dos pacotes GHCR esta registrada em devops.md."""
    devops_doc = (REPO_ROOT / "docs" / "development" / "devops.md").read_text(encoding="utf-8")
    assert "Visibilidade dos pacotes no GHCR" in devops_doc
    assert "nascem privados por padrão" in devops_doc
    assert "infra/docker-compose.ghcr.yml" in devops_doc
    assert "8080" in devops_doc


def test_cd_workflow_passes_required_settings_env_to_backend_container():
    """Garante que a validacao runtime do backend injeta as cinco envs obrigatorias de Settings."""
    cd_path = REPO_ROOT / ".github" / "workflows" / "cd.yml"
    data = yaml.safe_load(cd_path.read_text(encoding="utf-8"))

    steps = data["jobs"]["deploy"]["steps"]
    validate_step = next(s for s in steps if "Validar container de producao" in s.get("name", ""))
    run_script = validate_step["run"]
    for env_name in (
        "SECRET_KEY",
        "API_KEY",
        "POSTGRES_PASSWORD",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
    ):
        assert f"-e {env_name}" in run_script
    assert "import app.main" in run_script


def test_cd_and_release_please_enforce_ci_ok_gate_for_tag_sha():
    """Issue #171: deploy exige check 'CI OK' verde no SHA exato da tag antes de publicar."""
    cd_data = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text("utf-8"))
    rp_data = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "release-please.yml").read_text("utf-8")
    )

    verify_job = cd_data["jobs"]["verify-ci"]
    assert verify_job["if"] == "inputs.push || inputs.verify_ci"
    assert verify_job["permissions"]["checks"] == "read"
    verify_step = next(s for s in verify_job["steps"] if "CI OK" in s.get("name", ""))
    assert "scripts/verify_release_ci.py" in verify_step["run"]
    assert '--check-name "CI OK"' in verify_step["run"]

    deploy_job = cd_data["jobs"]["deploy"]
    assert deploy_job["needs"] == "verify-ci"

    rp_deploy = rp_data["jobs"]["deploy"]
    assert rp_deploy["permissions"]["checks"] == "read"
    assert rp_deploy["with"]["verify_ci"] is True


def test_verify_release_ci_blocks_failed_or_missing_and_allows_success():
    """Issue #171: testa o comportamento do gate de CI para aprovado, falho, ausente e pendente."""
    mod = _load_verify_release_ci()

    ok, msg = mod.verify_sha_ci(
        "conformia-bndes/conformia-platform",
        "a" * 40,
        fetcher=lambda *_: [
            {"id": 10, "name": "CI OK", "status": "completed", "conclusion": "success"}
        ],
    )
    assert ok is True
    assert "aprovado" in msg

    fail_missing, msg_missing = mod.verify_sha_ci(
        "conformia-bndes/conformia-platform",
        "b" * 40,
        fetcher=lambda *_: [],
    )
    assert fail_missing is False
    assert "Nenhum check-run" in msg_missing

    fail_red, msg_red = mod.verify_sha_ci(
        "conformia-bndes/conformia-platform",
        "c" * 40,
        fetcher=lambda *_: [
            {"id": 1, "name": "CI OK", "status": "completed", "conclusion": "success"},
            {"id": 2, "name": "CI OK", "status": "completed", "conclusion": "failure"},
        ],
    )
    assert fail_red is False
    assert "failure" in msg_red

    # Simula CI em execucao que conclui verde na segunda consulta
    responses = iter(
        [
            [{"id": 5, "name": "CI OK", "status": "in_progress", "conclusion": None}],
            [{"id": 5, "name": "CI OK", "status": "completed", "conclusion": "success"}],
        ]
    )
    slept = []
    ok_wait, _ = mod.verify_sha_ci(
        "conformia-bndes/conformia-platform",
        "d" * 40,
        wait_seconds=60,
        poll_interval=1,
        fetcher=lambda *_: next(responses),
        sleeper=lambda secs: slept.append(secs),
    )
    assert ok_wait is True
    assert len(slept) == 1


def test_governance_and_devops_docs_document_bypass_policy_and_release_runbook():
    """Issue #171: politica de bypass/excecoes e runbook reproduzivel de release documentados."""
    gov = (REPO_ROOT / "docs" / "development" / "governance.md").read_text(encoding="utf-8")
    devops = (REPO_ROOT / "docs" / "development" / "devops.md").read_text(encoding="utf-8")
    adr4 = (REPO_ROOT / "docs" / "architecture" / "adr-004-protecao-main-e-revisao.md").read_text(
        encoding="utf-8"
    )

    assert "bypass_mode" in gov and "pull_request" in gov
    assert "rulesets/24061709" in gov
    assert "Runbook Reproduzível de Release" in devops
    assert "verify_ci" in devops
    assert "AUD-17b" in adr4
