"""Document Extractor for PDFs using pdfplumber and Tesseract OCR fallback."""

import logging
import os
from typing import Dict, Any, List
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

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Executa extração completa de texto, tabelas e metadados de um arquivo PDF.
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

                    # Detecção de páginas digitalizadas (OCR fallback)
                    if len(page_text.strip()) < self.min_char_threshold:
                        logger.info(
                            f"Página {page_idx}/{total_pages} com pouco texto nativo ({len(page_text.strip())} chars). "
                            "Tentando extração OCR via Tesseract."
                        )
                        ocr_text = self._perform_ocr(page)
                        if ocr_text.strip():
                            page_text = ocr_text
                            is_scanned = True

                    extracted_pages.append({
                        "page_number": page_idx,
                        "text": page_text.strip(),
                        "tables": tables,
                        "is_scanned": is_scanned,
                        "char_count": len(page_text.strip()),
                    })
                    full_text_list.append(page_text.strip())

            full_text = "\n\n--- [QUEBRA DE PÁGINA] ---\n\n".join(full_text_list)

            return {
                "file_path": file_path,
                "metadata": {
                    "total_pages": len(extracted_pages),
                    "pdf_metadata": doc_metadata,
                    "has_scanned_pages": any(p["is_scanned"] for p in extracted_pages),
                },
                "pages": extracted_pages,
                "full_text": full_text,
            }

        except Exception as e:
            logger.error(f"Falha na extração documental do arquivo {file_path}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Erro ao extrair conteúdo do documento: {str(e)}") from e

    def _perform_ocr(self, page) -> str:
        """
        Executa OCR em uma página específica renderizada como imagem.
        """
        try:
            import pytesseract
            img = page.to_image(resolution=300).original
            text = pytesseract.image_to_string(img, lang=self.ocr_lang)
            return text
        except Exception as err:
            logger.warning(f"OCR indisponível ou falhou para a página {page.page_number}: {str(err)}")
            return ""
