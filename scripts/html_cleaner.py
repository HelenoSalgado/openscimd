"""Módulo de extração semântica e saneamento de documentos HTML legados.

Converte arquivos HTML legados (layout em tabelas, encoding ISO-8859-1/Windows-1252,
tags estilísticas arcaicas) para Markdown semântico de alta fidelidade editorial.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup, Tag


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
        text = re.sub(r"[\r\n\t]+", " ", text)
        return re.sub(r" {2,}", " ", text).strip()

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

        # Links internos de índice do site antigo
        if tag.name == "a":
            href = tag.get("href", "").lower()
            if any(ref in href for ref in ("sum-hugo.htm", "sumary.htm", "index.htm", "mailto:")):
                return True

        return False

    @classmethod
    def extract_metadata_from_soup(cls, soup: BeautifulSoup, default_title: str) -> dict[str, str]:
        """Extrai metadados do HTML (título da página, autoria e possíveis notas)."""
        title = default_title
        if soup.title and soup.title.string:
            title = cls.clean_text_whitespace(soup.title.string)

        author = "Hugo de São Vítor"
        if "tomas de aquino" in title.lower() and "genealogia" in title.lower():
            author = "Escola de São Vítor / Tradição Vitorina"

        return {
            "title": title,
            "author": author,
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
        processed_tables = set()

        for i, table in enumerate(tables):
            if table in processed_tables:
                continue

            cells = table.find_all("td")
            if not cells:
                continue

            table_text = cls.clean_text_whitespace(table.get_text())
            if not table_text:
                continue

            # Verifica se a tabela seguinte é uma referência bíblica alinhada (ex.: Salmo 61, 12)
            next_table = None
            if i + 1 < len(tables):
                candidate = tables[i + 1]
                cand_text = cls.clean_text_whitespace(candidate.get_text())
                # Verifica se é referência bíblica típica (Livro Cap, Vers)
                if re.match(
                    r"^(Salmo|Salmos|Mat\.|Mateus|Jo\.|João|Heb\.|Hebreus|Rom\.|Romanos|Apoc\.|Apocalipse|Hist\.|H\.E\.|Cor\.|1Cor\.|2Cor\.)\s+\d+",
                    cand_text,
                    re.IGNORECASE,
                ):
                    next_table = candidate

            if next_table is not None:
                # Criar blockquote semântico contendo citação + referência
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
                # Tabela de citação única centralizada
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
        # 1. Tratar <h4>: se contém tabelas, parágrafos ou elementos de bloco, é um container de layout arcaico
        for h4 in soup.find_all("h4"):
            if h4.find_all(["table", "p", "div", "h2", "h3"]):
                h4.unwrap()
            else:
                text = cls.clean_text_whitespace(h4.get_text())
                if len(text) > 80 or text.endswith((".", ":", ";", "?", "!")):
                    p = soup.new_tag("p")
                    p.string = text
                    h4.replace_with(p)
                elif not text:
                    h4.decompose()

        # 2. Descartar <h2> que sejam apenas cabeçalho de topo de página (Nome do Autor repetido ou título redundante)
        for h2 in soup.find_all("h2"):
            text = cls.clean_text_whitespace(h2.get_text()).lower()
            if text in ("hugo de são vítor", "hugo de sao vitor", "hugo de s. vitor"):
                h2.decompose()

        # 3. Remover <h5> vazios ou de formatação espúria
        for h5 in soup.find_all("h5"):
            text = cls.clean_text_whitespace(h5.get_text())
            if not text or cls.is_navigation_element(h5):
                h5.decompose()

    @classmethod
    def clean_html_document(cls, html_content: str, default_title: str = "Sem Título") -> tuple[dict[str, str], str]:
        """Executa a limpeza semântica do documento HTML e retorna metadados e Markdown limpo."""
        # 0. Pré-processamento: forçar fechamento de tags <p> em HTML 4 legado
        processed_html = re.sub(r"(?i)<p\b[^>]*>", "</p><p>", html_content)
        processed_html = re.sub(r"(?i)<(table|h[1-6])\b", r"</p><\1", processed_html)

        soup = BeautifulSoup(processed_html, "html.parser")

        # 1. Extrair metadados
        metadata = cls.extract_metadata_from_soup(soup, default_title)

        # 2. Remover elementos supérfluos (scripts, styles, comentários)
        for tag in soup.find_all(["script", "style", "iframe", "frame"]):
            tag.decompose()

        # 3. Remover nós de navegação e rodapés legados
        for tag in soup.find_all(["p", "div", "h2", "h3", "h4", "h5", "table", "a", "center"]):
            if cls.is_navigation_element(tag):
                tag.decompose()

        # 4. Saneamento prévio de containers de layout <h4>
        for h4 in soup.find_all("h4"):
            if h4.find_all(["table", "p", "div", "h2", "h3"]):
                h4.unwrap()

        # 5. Tratar tabelas de citação bíblica
        cls.convert_tables_to_blockquotes(soup)

        # 6. Desempacotar tabelas de margem restantes
        for tag in soup.find_all(["table", "tbody", "thead", "tfoot", "tr", "th", "td"]):
            tag.unwrap()

        # 7. Desempacotar tags de fonte e estilo semântico redundante
        for tag in soup.find_all(["font", "center"]):
            tag.unwrap()

        # 8. Saneamento de cabeçalhos
        cls.sanitize_headings(soup)

        # 9. Converter HTML limpo em Markdown
        markdown_body = cls.soup_to_clean_markdown(soup)

        return metadata, markdown_body

    @classmethod
    def soup_to_clean_markdown(cls, soup: BeautifulSoup) -> str:
        """Converte o soup semântico saneado em blocos Markdown puros."""
        blocks: list[str] = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "blockquote", "hr"]):
            # Se o elemento for um <p> já contido em um <blockquote>, não o processe duas vezes
            if element.name == "p" and element.find_parent("blockquote"):
                continue

            if element.name == "hr":
                # Evita acúmulo de réguas horizontais
                if blocks and blocks[-1] != "---":
                    blocks.append("---")
                continue

            if element.name == "blockquote":
                # Formatar blockquote
                bq_paragraphs = element.find_all("p")
                if bq_paragraphs:
                    bq_lines = []
                    for p in bq_paragraphs:
                        text = cls.clean_text_whitespace(p.get_text())
                        if text:
                            bq_lines.append(f"> {text}")
                    if bq_lines:
                        blocks.append("\n>\n".join(bq_lines))
                else:
                    text = cls.clean_text_whitespace(element.get_text())
                    if text:
                        blocks.append(f"> {text}")
                continue

            text = cls.clean_text_whitespace(element.get_text())
            if not text:
                continue

            if element.name == "h1":
                blocks.append(f"# {text}")
            elif element.name == "h2":
                blocks.append(f"## {text}")
            elif element.name == "h3":
                blocks.append(f"### {text}")
            elif element.name == "h4":
                blocks.append(f"#### {text}")
            elif element.name == "p":
                # Normaliza aspas escapadas que possam ter vindo do HTML
                clean_p = text.replace('\\"', '"').replace("\\'", "'")
                blocks.append(clean_p)

        # Normalização de blocos consecutivos e remoção de linhas vazias repetidas
        result = "\n\n".join(blocks).strip()

        # Higienização final de resíduos de barras invertidas e caracteres de escape
        result = re.sub(r'\\+(["\'])', r"\1", result)
        result = re.sub(r'\\+\n', "\n", result)
        return result

    @classmethod
    def convert_file(
        cls,
        input_file: str | Path,
        output_file: str | Path,
        part_title: Optional[str] = None,
    ) -> Path:
        """Lê um arquivo HTML legado, saneia o conteúdo e grava em Markdown com Frontmatter."""
        in_path = Path(input_file).resolve()
        out_path = Path(output_file).resolve()

        if not in_path.exists():
            raise FileNotFoundError(f"Arquivo de origem não encontrado: {in_path}")

        with open(in_path, "rb") as f:
            raw_bytes = f.read()

        html_str = cls.decode_html_bytes(raw_bytes)
        default_title = part_title or in_path.stem
        metadata, body_md = cls.clean_html_document(html_str, default_title=default_title)

        if part_title:
            metadata["title"] = part_title

        frontmatter = (
            f"---\n"
            f'title: "{metadata["title"]}"\n'
            f'author: "{metadata["author"]}"\n'
            f'language: "{metadata["language"]}"\n'
            f'license: "{metadata["license"]}"\n'
            f"---\n\n"
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + body_md + "\n")

        return out_path
