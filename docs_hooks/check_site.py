"""
Hook do MkDocs que verifica o site gerado (on_post_build).

O `mkdocs build --strict` valida links escritos em Markdown, mas nao os links em HTML bruto
(como os cartoes da pagina inicial) nem o que o tema injeta. Este hook le o HTML final e falha
o build quando encontra:

- link interno que nao corresponde a nenhum arquivo do site;
- link com esquema `javascript:`;
- script carregado de outro dominio (todo JavaScript deve ser servido pelo proprio site);
- pagina de conteudo sem exatamente um `<h1>`.

Roda em todo build (local, CI e publicacao), sem dependencias alem da biblioteca padrao.
"""

from __future__ import annotations

import posixpath
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from mkdocs.exceptions import PluginError

# Arquivos gerados pelo tema ou pelo build que nao sao paginas de conteudo.
NON_CONTENT_PAGES = {"404.html", "search.html"}


class _PageScanner(HTMLParser):
    """Coleta scripts da pagina inteira e links e titulos apenas do conteudo (<article>)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.h1_count = 0
        self._article_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "article":
            self._article_depth += 1
        if not self._article_depth:
            return
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "h1":
            self.h1_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self._article_depth:
            self._article_depth -= 1


def _resolve(site_dir: Path, page: Path, href: str) -> Path | None:
    """Converte um href interno no arquivo esperado dentro de site_dir (None se externo)."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    if parts.path.startswith("/"):
        # Links absolutos do tema incluem o prefixo de site_url (/conformia-platform/).
        return None
    page_dir = page.parent.relative_to(site_dir).as_posix()
    target = posixpath.normpath(posixpath.join(page_dir, unquote(parts.path)))
    resolved = site_dir / target
    if parts.path.endswith("/") or resolved.is_dir():
        resolved = resolved / "index.html"
    return resolved


def on_post_build(config, **kwargs) -> None:
    site_dir = Path(config["site_dir"])
    problems: list[str] = []

    for page in sorted(site_dir.rglob("*.html")):
        relative = page.relative_to(site_dir).as_posix()
        scanner = _PageScanner()
        scanner.feed(page.read_text(encoding="utf-8"))

        for href in scanner.links:
            if href.strip().lower().startswith("javascript:"):
                problems.append(f"{relative}: link javascript: proibido ({href})")
                continue
            target = _resolve(site_dir, page, href)
            if target is not None and not target.is_file():
                problems.append(f"{relative}: link interno quebrado -> {href}")

        for src in scanner.scripts:
            if urlsplit(src).netloc:
                problems.append(f"{relative}: script de dominio externo -> {src}")

        if relative not in NON_CONTENT_PAGES and scanner.h1_count != 1:
            problems.append(f"{relative}: esperado 1 <h1>, encontrados {scanner.h1_count}")

    if problems:
        detail = "\n  ".join(problems)
        raise PluginError(f"Verificacao do site falhou ({len(problems)} problemas):\n  {detail}")
