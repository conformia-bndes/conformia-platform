"""Testes de endurecimento do upload"""

import io
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import documents

PDF_MINIMO = b"%PDF-1.4\n%conteudo de teste\n"


class SpyFile(io.BytesIO):
    """Registra o tamanho pedido em cada read()."""

    def __init__(self, data: bytes):
        super().__init__(data)
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class BrokenFile:
    def read(self, size=-1):
        raise OSError("/segredo/interno/caminho.tmp: disco com defeito")


def _fake_upload(file_obj, filename="doc.pdf"):
    return SimpleNamespace(filename=filename, file=file_obj, content_type="application/pdf")


def test_leitura_limitada_a_max_mais_um(monkeypatch):
    """Nunca le mais que MAX_FILE_SIZE + 1 bytes, mesmo com arquivo muito maior."""
    monkeypatch.setattr(documents, "MAX_FILE_SIZE", 1024)
    spy = SpyFile(b"%PDF" + b"0" * 5000)

    with pytest.raises(HTTPException) as exc:
        documents.upload_document(file=_fake_upload(spy), async_process=False, db=None)

    assert exc.value.status_code == 413
    assert spy.read_sizes == [1025]


def test_upload_acima_do_limite_retorna_413(client, monkeypatch):
    monkeypatch.setattr(documents, "MAX_FILE_SIZE", 1024)
    payload = b"%PDF" + b"0" * 1021  # 1025 bytes

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("grande.pdf", payload, "application/pdf")},
    )
    assert resp.status_code == 413


def test_upload_exatamente_no_limite_nao_e_barrado_por_tamanho(client, monkeypatch):
    monkeypatch.setattr(documents, "MAX_FILE_SIZE", 1024)
    payload = b"X" * 1024  # no limite, mas sem assinatura PDF

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("limite.pdf", payload, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "assinatura binaria" in resp.json()["detail"]  # barrou na assinatura, nao no tamanho


def test_falha_de_leitura_nao_vaza_detalhe():
    with pytest.raises(HTTPException) as exc:
        documents.upload_document(file=_fake_upload(BrokenFile()), async_process=False, db=None)

    assert exc.value.status_code == 400
    assert "segredo" not in exc.value.detail
    assert "disco com defeito" not in exc.value.detail


def test_falha_de_gravacao_retorna_500_generico(client, monkeypatch, tmp_path, caplog):
    """Diretorio inexistente forca erro de gravacao: cliente recebe frase fixa."""
    monkeypatch.setattr(documents, "UPLOAD_DIR", str(tmp_path / "nao_existe"))

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("ok.pdf", PDF_MINIMO, "application/pdf")},
    )

    assert resp.status_code == 500
    assert resp.json()["detail"] == "Falha ao processar o upload."
    assert "nao_existe" not in resp.text
    assert "Errno" not in resp.text
    assert "nao_existe" in caplog.text  # o detalhe tecnico ficou no log
