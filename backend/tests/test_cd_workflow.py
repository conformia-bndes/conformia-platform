"""Testes para o workflow de CD (cd.yml) e compose de imagens GHCR (Issue #102)."""

from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


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
