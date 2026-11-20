"""Módulo de extração semântica e saneamento de documentos HTML legados.

Converte arquivos HTML legados (layout em tabelas, encoding ISO-8859-1/Windows-1252,
tags estilísticas arcaicas) para Markdown semântico de alta fidelidade editorial.
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, PageElement, Tag

_VITORINO_HINTS: tuple[str, ...] = ("hugo de são vítor", "hugo de sao vitor", "hugo de s. vitor", "sum-hugo")


class LegacyHtmlCleaner:
    """Parser especialista para saneamento e conversão semântica de HTMLs legados."""

    @staticmethod
    def decode_html_bytes(raw_bytes: bytes) -> str:
        """Decodifica os bytes brutos do arquivo tentando diferentes encodings."""
        for enc in ("utf-8", "windows-1252", "iso-8859-1"):
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw_bytes.decode("latin-1", errors="replace")

    @classmethod
    def clean_text_whitespace(cls, text: str) -> str:
        """Remove quebras de linha e espaços múltiplos de um segmento de texto."""
        cleaned = re.sub(r"[\r\n\t]+", " ", text)
        return re.sub(r" {2,}", " ", cleaned).strip()

    @classmethod
    def render_inline_markdown(cls, element: Tag) -> str:
        """Converte filhos inline (<i>, <em>, <b>, <strong>) preservando ênfases Markdown."""

        def _walk(node: PageElement) -> str:
            if isinstance(node, Comment):
                return ""
            if isinstance(node, NavigableString):
                return re.sub(r"[\r\n\t]+", " ", str(node))
            if not isinstance(node, Tag):
                return ""

            tag_name = (node.name or "").lower()
            inner = "".join(_walk(child) for child in node.children)
            if not inner:
                return ""

            if tag_name in ("i", "em"):
                stripped = inner.strip()
                if not stripped:
                    return " "
                lead = " " if inner[0].isspace() else ""
                trail = " " if inner[-1].isspace() else ""
                return f"{lead}*{stripped}*{trail}"

            if tag_name in ("b", "strong"):
                stripped = inner.strip()
                if not stripped:
                    return " "
                lead = " " if inner[0].isspace() else ""
                trail = " " if inner[-1].isspace() else ""
                return f"{lead}**{stripped}**{trail}"

            if tag_name == "br":
                return " "

            return inner

        raw = _walk(element)
        # Corrige casos aninhados de ***...*** com espaços extras e normaliza espaços múltiplos
        raw = re.sub(r"\*{4,}", "**", raw)
        return re.sub(r" {2,}", " ", raw).strip()

    @classmethod
    def is_navigation_element(cls, tag: Tag) -> bool:
        """Determina se uma tag representa elemento de navegação ou rodapé do site legado."""
        text = tag.get_text().strip().lower()
        if not text:
            return False

        nav_keywords = {
            "índice da página",
            "indice da pagina",
            "índice geral da página",
            "indice geral da pagina",
            "índice geral",
            "indice geral",
            "sum-hugo.htm",
            "sumary.htm",
            "início",
            "inicio",
            "página principal",
        }

        if text in nav_keywords or any(kw in text for kw in ("sum-hugo", "sumary.htm")):
            return True

        if tag.name == "a":
            href = str(tag.get("href", "")).lower()
            if any(ref in href for ref in ("sum-hugo.htm", "sumary.htm", "index.htm", "mailto:")):
                return True

        return False

    @classmethod
    def extract_metadata_from_soup(
        cls,
        soup: BeautifulSoup,
        default_title: str,
        author: str | None = None,
    ) -> dict[str, str]:
        """Extrai metadados do HTML (título da página, meta author ou autoria explícita)."""
        title = default_title
        if soup.title and soup.title.string:
            title = cls.clean_text_whitespace(soup.title.string)

        resolved_author = (author or "").strip()
        if not resolved_author:
            meta_author = soup.find("meta", attrs={"name": re.compile(r"^author$", re.IGNORECASE)})
            if isinstance(meta_author, Tag) and meta_author.get("content"):
                resolved_author = cls.clean_text_whitespace(str(meta_author["content"]))

        if not resolved_author:
            page_text_lower = soup.get_text(" ", strip=True).lower()
            raw_html_lower = str(soup).lower()
            if "tomas de aquino" in title.lower() and "genealogia" in title.lower():
                resolved_author = "Escola de São Vítor / Tradição Vitorina"
            elif any(hint in page_text_lower or hint in raw_html_lower for hint in _VITORINO_HINTS):
                resolved_author = "Hugo de São Vítor"
            else:
                resolved_author = "Desconhecido"

        return {
            "title": title,
            "author": resolved_author,
            "language": "pt-BR",
            "license": "CC BY-NC 4.0",
        }

    @classmethod
    def strip_outer_quotes(cls, text: str) -> str:
        """Remove aspas das extremidades preservando a pontuação correta."""
        t = text.strip()
        t = re.sub(r'^["“\'\s]+', "", t)
        t = re.sub(r'["”\']\s*\.\s*$', ".", t)
        t = re.sub(r'\.\s*["”\']\s*$', ".", t)
        t = re.sub(r'["”\'\s]+$', "", t)
        return t.strip()

    @classmethod
    def convert_tables_to_blockquotes(cls, soup: BeautifulSoup) -> None:
        """Identifica tabelas de citação bíblica e de referência e as converte em blockquotes."""
        tables = soup.find_all("table")
        processed_tables: set[Tag] = set()

        for idx, table in enumerate(tables):
            if table in processed_tables:
                continue

            cells = table.find_all("td")
            if not cells:
                continue

            table_text = cls.clean_text_whitespace(table.get_text())
            if not table_text:
                continue

            next_table: Tag | None = None
            if idx + 1 < len(tables):
                candidate = tables[idx + 1]
                cand_text = cls.clean_text_whitespace(candidate.get_text())
                if re.match(
                    r"^(Salmo|Salmos|Mat\.|Mateus|Jo\.|João|Heb\.|Hebreus|Rom\.|Romanos|Apoc\.|Apocalipse|Hist\.|H\.E\.|Cor\.|1Cor\.|2Cor\.)\s+\d+",
                    cand_text,
                    re.IGNORECASE,
                ):
                    next_table = candidate

            if next_table is not None:
                quote_text = cls.strip_outer_quotes(table_text)
                ref_text = cls.clean_text_whitespace(next_table.get_text()).strip()

                bq = soup.new_tag("blockquote")
                p_quote = soup.new_tag("p")
                p_quote.string = f"“{quote_text}”"
                bq.append(p_quote)

                p_ref = soup.new_tag("p")
                p_ref.string = f"— {ref_text}"
                bq.append(p_ref)

                table.replace_with(bq)
                next_table.decompose()
                processed_tables.add(table)
                processed_tables.add(next_table)
            elif (
                len(cells) == 1
                and cells[0].get("align") == "center"
                and (table_text.startswith(('"', "“")) or len(table_text) < 300)
                and not any(tag in table_text.lower() for tag in ("hugo de", "índice"))
            ):
                quote_text = cls.strip_outer_quotes(table_text)
                bq = soup.new_tag("blockquote")
                p_quote = soup.new_tag("p")
                p_quote.string = f"“{quote_text}”"
                bq.append(p_quote)
                table.replace_with(bq)
                processed_tables.add(table)

    @classmethod
    def sanitize_headings(cls, soup: BeautifulSoup) -> None:
        """Desfaz o uso indevido de <h4> para parágrafos corridos e normaliza cabeçalhos reais."""
        for h4 in soup.find_all("h4"):
            if h4.find_all(["table", "p", "div", "h2", "h3"]):
                h4.unwrap()
            else:
                text = cls.clean_text_whitespace(h4.get_text())
                if len(text) > 80 or text.endswith((".", ":", ";", "?", "!")):
                    p = soup.new_tag("p")
                    p.extend(list(h4.contents))
                    h4.replace_with(p)
                elif not text:
                    h4.decompose()

        for h2 in soup.find_all("h2"):
            text = cls.clean_text_whitespace(h2.get_text()).lower()
            if text in ("hugo de são vítor", "hugo de sao vitor", "hugo de s. vitor"):
                h2.decompose()

        for h5 in soup.find_all("h5"):
            text = cls.clean_text_whitespace(h5.get_text())
            if not text or cls.is_navigation_element(h5):
                h5.decompose()

    @classmethod
    def clean_html_document(
        cls,
        html_content: str,
        default_title: str = "Sem Título",
        author: str | None = None,
    ) -> tuple[dict[str, str], str]:
        """Executa a limpeza semântica do documento HTML e retorna metadados e Markdown limpo."""
        processed_html = re.sub(r"(?i)<p\b[^>]*>", "</p><p>", html_content)
        processed_html = re.sub(r"(?i)<(table|h[1-6])\b", r"</p><\1", processed_html)

        soup = BeautifulSoup(processed_html, "html.parser")
        metadata = cls.extract_metadata_from_soup(soup, default_title, author=author)

        for tag in soup.find_all(["script", "style", "iframe", "frame"]):
            tag.decompose()

        for tag in soup.find_all(["p", "div", "h2", "h3", "h4", "h5", "table", "a", "center"]):
            if cls.is_navigation_element(tag):
                tag.decompose()

        for h4 in soup.find_all("h4"):
            if h4.find_all(["table", "p", "div", "h2", "h3"]):
                h4.unwrap()

        cls.convert_tables_to_blockquotes(soup)

        for tag in soup.find_all(["table", "tbody", "thead", "tfoot", "tr", "th", "td"]):
            tag.unwrap()

        for tag in soup.find_all(["font", "center"]):
            tag.unwrap()

        cls.sanitize_headings(soup)
        markdown_body = cls.soup_to_clean_markdown(soup)

        return metadata, markdown_body

    @classmethod
    def soup_to_clean_markdown(cls, soup: BeautifulSoup) -> str:
        """Converte o soup semântico saneado em blocos Markdown puros."""
        blocks: list[str] = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "blockquote", "hr"]):
            if element.name == "p" and element.find_parent("blockquote"):
                continue

            if element.name == "hr":
                if blocks and blocks[-1] != "---":
                    blocks.append("---")
                continue

            if element.name == "blockquote":
                bq_paragraphs = element.find_all("p")
                if bq_paragraphs:
                    bq_lines: list[str] = []
                    for p in bq_paragraphs:
                        p_text = cls.render_inline_markdown(p)
                        if p_text:
                            bq_lines.append(f"> {p_text}")
                    if bq_lines:
                        blocks.append("\n>\n".join(bq_lines))
                else:
                    bq_text = cls.render_inline_markdown(element)
                    if bq_text:
                        blocks.append(f"> {bq_text}")
                continue

            if element.name in ("h1", "h2", "h3", "h4"):
                heading_text = cls.clean_text_whitespace(element.get_text())
                if not heading_text:
                    continue
                prefix = "#" * int(element.name[1])
                blocks.append(f"{prefix} {heading_text}")
            elif element.name == "p":
                p_md = cls.render_inline_markdown(element)
                if not p_md:
                    continue
                clean_p = p_md.replace('\\"', '"').replace("\\'", "'")
                blocks.append(clean_p)

        result = "\n\n".join(blocks).strip()
        result = re.sub(r'\\+(["\'])', r"\1", result)
        result = re.sub(r"\\+\n", "\n", result)
        return result

    @classmethod
    def convert_file(
        cls,
        input_file: str | Path,
        output_file: str | Path,
        part_title: str | None = None,
        author: str | None = None,
    ) -> Path:
        """Lê um arquivo HTML legado, saneia o conteúdo e grava em Markdown com Frontmatter."""
        in_path = Path(input_file).resolve()
        out_path = Path(output_file).resolve()

        if not in_path.exists():
            raise FileNotFoundError(f"Arquivo de origem não encontrado: {in_path}")

        raw_bytes = in_path.read_bytes()
        html_str = cls.decode_html_bytes(raw_bytes)
        default_title = part_title or in_path.stem
        metadata, body_md = cls.clean_html_document(html_str, default_title=default_title, author=author)

        if part_title:
            metadata["title"] = part_title

        frontmatter = (
            "---\n"
            f'title: "{metadata["title"]}"\n'
            f'author: "{metadata["author"]}"\n'
            f'language: "{metadata["language"]}"\n'
            f'license: "{metadata["license"]}"\n'
            "---\n\n"
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(frontmatter + body_md + "\n", encoding="utf-8")
        return out_path
