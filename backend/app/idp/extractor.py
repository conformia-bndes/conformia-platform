"""Document Extractor for PDFs using pdfplumber and Tesseract OCR fallback."""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """
    Motor de extração híbrido:
    - Extração textual e tabular nativa via pdfplumber.
    - OCR via Tesseract para páginas digitalizadas (scanned) ou com baixa densidade textual.
    """

    def __init__(self, min_char_threshold: int = 50, ocr_lang: str = "por"):
        self.min_char_threshold = min_char_threshold
        self.ocr_lang = ocr_lang

    def extract(self, file_path: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa extração completa de texto, tabelas e metadados de um arquivo PDF.

        Erros por página ficam em `pages[i]["error"]` (formato ErrorDetail: code, message,
        details) e em `metadata["page_errors"]`. Se NENHUMA página tiver texto legível, ou
        se o documento inteiro falhar, lança RuntimeError com mensagem legível.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        extracted_pages: List[Dict[str, Any]] = []
        full_text_list: List[str] = []
        doc_metadata: Dict[str, Any] = {}

        try:
            with pdfplumber.open(file_path) as pdf:
                doc_metadata = pdf.metadata or {}
                total_pages = len(pdf.pages)

                for page_idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    is_scanned = False
                    extraction_method = "native"
                    ocr_attempted = False
                    page_error: Optional[Dict[str, Any]] = None

                    # Detecção de páginas digitalizadas (OCR fallback)
                    if len(page_text.strip()) < self.min_char_threshold:
                        ocr_attempted = True
                        logger.info(
                            f"Pagina {page_idx}/{total_pages} com pouco texto nativo "
                            f"({len(page_text.strip())} chars). "
                            "Acionando fallback OCR via Tesseract."
                        )
                        ocr_text, ocr_error = self._perform_ocr(page, page_idx)
                        if ocr_text.strip():
                            page_text = ocr_text
                            is_scanned = True
                            extraction_method = "ocr"
                        elif ocr_error:
                            page_error = {
                                "code": "OCR_FAILED",
                                "message": ocr_error,
                                "details": {"page": page_idx, "stage": "ocr"},
                            }
                        elif not page_text.strip():
                            page_error = {
                                "code": "EMPTY_PAGE",
                                "message": (
                                    f"Pagina {page_idx} sem texto legivel " "(nativo e OCR vazios)."
                                ),
                                "details": {"page": page_idx, "stage": "ocr"},
                            }

                    extracted_pages.append(
                        {
                            "page_number": page_idx,
                            "text": page_text.strip(),
                            "tables": tables,
                            "is_scanned": is_scanned,
                            "char_count": len(page_text.strip()),
                            "extraction_method": extraction_method,
                            "ocr_attempted": ocr_attempted,
                            "error": page_error,
                        }
                    )
                    full_text_list.append(page_text.strip())

            full_text = "\n\n--- [QUEBRA DE PÁGINA] ---\n\n".join(full_text_list)
            page_errors = [p["error"] for p in extracted_pages if p["error"]]

            if extracted_pages and len(page_errors) == len(extracted_pages):
                raise ValueError("Nenhuma pagina com texto legivel. " + page_errors[0]["message"])

            return {
                "document_id": document_id,
                "file_path": file_path,
                "metadata": {
                    "total_pages": len(extracted_pages),
                    "pdf_metadata": doc_metadata,
                    "has_scanned_pages": any(p["is_scanned"] for p in extracted_pages),
                    "page_errors": page_errors,
                },
                "pages": extracted_pages,
                "full_text": full_text,
            }

        except Exception as e:
            logger.error(
                f"Falha na extração documental do arquivo {file_path}: {str(e)}",
                exc_info=True,
            )
            raise RuntimeError(f"Erro ao extrair conteúdo do documento: {str(e)}") from e

    def _perform_ocr(self, page, page_idx: int) -> Tuple[str, Optional[str]]:
        """
        Executa OCR em uma página renderizada como imagem.
        Retorna (texto, erro): erro é None quando o OCR rodou sem exceção.
        """
        try:
            import pytesseract

            img = page.to_image(resolution=300).original
            return pytesseract.image_to_string(img, lang=self.ocr_lang), None
        except Exception as err:
            message = f"OCR falhou na pagina {page_idx}: {str(err)}"
            logger.warning(message)
            return "", message
