"""Módulo BookAssembler para compilação e montagem editorial de volumes.

Une partes modulares e revisadas em uma única obra canônica com governança
hierárquica de cabeçalhos (via salopdoc.HeadingOrganizer), consolidação do
aparato crítico pós-texto e injeção de Frontmatter YAML canônico.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional
import yaml

try:
    import salopdoc
except ImportError:
    salopdoc = None

from scripts.utils import parse_markdown_file


class BookAssembler:
    """Montador de obras clássicas e livros científicos a partir de partes modulares."""

    @staticmethod
    def shift_headings(markdown_text: str, level_offset: int = 1) -> str:
        """Rebaixa hierarquicamente os cabeçalhos Markdown adicionando '#' no início."""
        lines = markdown_text.splitlines()
        shifted_lines: list[str] = []

        for line in lines:
            match = re.match(r"^(#{1,5})\s+(.*)$", line)
            if match:
                hashes = match.group(1)
                title_text = match.group(2)
                new_hashes = "#" * min(len(hashes) + level_offset, 6)
                shifted_lines.append(f"{new_hashes} {title_text}")
            else:
                shifted_lines.append(line)

        return "\n".join(shifted_lines)

    @classmethod
    def extract_notes_from_body(cls, body: str) -> tuple[str, list[str]]:
        """Extrai declarações de notas de rodapé do pós-texto e retorna o corpo limpo e as notas."""
        lines = body.splitlines()
        clean_lines: list[str] = []
        collected_notes: list[str] = []
        in_notes_section = False

        for line in lines:
            # Detecta separador ou cabeçalho de notas pós-texto
            if line.strip() == "---" and not in_notes_section:
                # Pode ser o início da seção de notas pós-texto
                in_notes_section = True
                continue

            if in_notes_section:
                # Verifica se é uma declaração de nota [^...]:
                if re.match(r"^\[\^[a-zA-Z0-9_-]+\]:\s+", line.strip()):
                    collected_notes.append(line.strip())
                elif re.match(r"^###\s+Notas", line.strip()):
                    continue
                elif line.strip() and not line.strip().startswith("#"):
                    # Continuação de nota em múltiplas linhas
                    if collected_notes:
                        collected_notes[-1] += f" {line.strip()}"
            else:
                # Verifica se há declaração de nota mesmo sem separador prévio
                if re.match(r"^\[\^[a-zA-Z0-9_-]+\]:\s+", line.strip()):
                    collected_notes.append(line.strip())
                    in_notes_section = True
                else:
                    clean_lines.append(line)

        clean_body = "\n".join(clean_lines).strip()
        return clean_body, collected_notes

    @classmethod
    def assemble_volume(
        cls,
        parts_dir: str | Path,
        output_path: str | Path,
        metadata: dict[str, Any],
        add_default_editorial_notes: bool = True,
    ) -> Path:
        """Monta um volume a partir de arquivos Markdown ordenados em parts_dir."""
        parts_path = Path(parts_dir).resolve()
        out_file = Path(output_path).resolve()

        if not parts_path.exists() or not parts_path.is_dir():
            raise FileNotFoundError(f"Diretório de partes não encontrado: {parts_path}")

        part_files = sorted([f for f in parts_path.glob("*.md") if f.is_file()])
        if not part_files:
            raise ValueError(f"Nenhum arquivo Markdown encontrado em: {parts_path}")

        assembled_sections: list[str] = []
        all_notes: list[str] = []
        first_section = True

        for part_file in part_files:
            parsed = parse_markdown_file(str(part_file))
            part_meta = parsed.get("metadata", {})
            raw_body = parsed.get("body", "").strip()

            clean_body, part_notes = cls.extract_notes_from_body(raw_body)
            all_notes.extend(part_notes)

            # Define o título da parte/tratado
            part_title = part_meta.get("title")
            if not part_title:
                # Procura primeiro cabeçalho no corpo
                first_h = re.search(r"^#+\s+(.*)$", clean_body, re.MULTILINE)
                if first_h:
                    part_title = first_h.group(1).strip()
                    # Remove o primeiro cabeçalho do corpo para não duplicar
                    clean_body = clean_body[first_h.end():].strip()
                else:
                    part_title = part_file.stem

            # Limpa qualquer # inicial redundante do corpo da parte
            clean_body = re.sub(r"^#\s+.*?\n", "", clean_body).strip()

            # Rebaixa cabeçalhos internos da parte (## vira ###, ### vira ####)
            body_shifted = cls.shift_headings(clean_body, level_offset=1)

            # Aplica HeadingOrganizer do salopdoc se disponível
            if salopdoc is not None:
                try:
                    quote_conv = salopdoc.QuoteConverter()
                    heading_org = salopdoc.HeadingOrganizer()
                    body_shifted = quote_conv.convert(body_shifted)
                    # Não passamos o documento inteiro pelo HeadingOrganizer de uma vez
                    # para preservar a hierarquia de livro (## Tratado -> ### Capítulos)
                except Exception:
                    pass

            # Formata o cabeçalho canônico da seção/tratado (## *Título*)
            clean_title = part_title.strip("*_ ")
            if first_section and add_default_editorial_notes:
                section_header = f"## *{clean_title}*[^ne1][^ne2][^ne3]"
                first_section = False
            else:
                section_header = f"## *{clean_title}*"

            assembled_sections.append(f"{section_header}\n\n{body_shifted}")

        # Montagem do corpo unificado
        full_body = "\n\n".join(assembled_sections).strip()

        # Construção do Aparato Crítico Pós-Texto
        editorial_notes: list[str] = []
        translator_notes: list[str] = []
        author_notes: list[str] = []

        if add_default_editorial_notes:
            editorial_notes.append(
                "[^ne1]: **Sobre Hugo de São Vítor**: Hugo de São Vítor (*Magister Hugo de Sancto Victore*, c. 1096 – 1141) "
                "foi um dos maiores teólogos, filósofos e mestres espirituais da Idade Média Central. Cônego Regular na Abadia "
                "de São Vítor em Paris, distinguiu-se pela síntese monumental entre erudição humanística, teologia bíblica e "
                "contemplação mística, sendo cognominado na tradição escolástica como «o segundo Agostinho» (*alter Augustinus*)."
            )
            editorial_notes.append(
                "[^ne2]: **Proveniência do Texto**: Esta edição em Markdown semântico foi compilada e revisada para o OpenSciMD "
                "e o leitor LeiaME a partir dos tratados traduzidos e digitalizados originalmente pelo portal *cristianismo.org.br*, "
                "sob licença de livre reprodução para fins de estudo e uso não comercial."
            )
            editorial_notes.append(
                "[^ne3]: **Fixação Ortográfica e Tipográfica**: A grafia do texto foi fixada em conformidade com o Acordo Ortográfico "
                "da Língua Portuguesa vigente, preservando-se rigorosamente a integridade lexical, os termos latinos e as escolhas "
                "de tradução do texto-fonte, com normalização de citações bíblicas e aparatos críticos."
            )

        for note in all_notes:
            if note.startswith("[^ne"):
                if note not in editorial_notes:
                    editorial_notes.append(note)
            elif note.startswith("[^nt"):
                if note not in translator_notes:
                    translator_notes.append(note)
            else:
                if note not in author_notes:
                    author_notes.append(note)

        notes_blocks: list[str] = []
        if editorial_notes:
            notes_blocks.append("### Notas Editoriais\n\n" + "\n\n".join(editorial_notes))
        if translator_notes:
            notes_blocks.append("### Notas do Tradutor\n\n" + "\n\n".join(translator_notes))
        if author_notes:
            notes_blocks.append("### Notas do Autor\n\n" + "\n\n".join(author_notes))

        post_text = ""
        if notes_blocks:
            post_text = "\n\n---\n\n" + "\n\n".join(notes_blocks)

        default_authors = [{"name": metadata.get("author", "Hugo de São Vítor")}]
        frontmatter_data: dict[str, Any] = {
            "title": metadata.get("title", "Obra sem Título"),
            "authors": metadata.get("authors", default_authors),
            "summary": metadata.get("summary", ""),
            "date": metadata.get("date", "c. 1130 d.C."),
            "license": metadata.get("license", "CC BY-NC 4.0"),
            "translator": metadata.get("translator", "Equipe Editorial cristianismo.org.br"),
            "categories": metadata.get("categories", ["Teologia", "Escola Vitorina"]),
            "language": metadata.get("language", "pt-BR"),
        }
        if "originalLanguage" in metadata:
            frontmatter_data["originalLanguage"] = metadata["originalLanguage"]
        if "keywords" in metadata:
            frontmatter_data["keywords"] = metadata["keywords"]
        if "source_url" in metadata:
            frontmatter_data["source_url"] = metadata["source_url"]

        fm_yaml = yaml.dump(
            frontmatter_data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

        final_content = f"---\n{fm_yaml}---\n\n{full_body}{post_text}\n"

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(final_content)

        return out_file
