"""Módulo BookAssembler para compilação e montagem editorial de volumes.

Une partes modulares e revisadas em uma única obra canônica com governança
hierárquica de cabeçalhos, consolidação do aparato crítico pós-texto e
injeção de Frontmatter YAML canônico.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

try:
    import salopdoc
except ImportError:
    salopdoc = None

from scripts.utils import parse_markdown_file

_HUGO_VITOR_EDITORIAL_NOTES: tuple[str, ...] = (
    "[^ne1]: **Sobre Hugo de São Vítor**: Hugo de São Vítor (*Magister Hugo de Sancto Victore*, c. 1096 – 1141) "
    "foi um dos maiores teólogos, filósofos e mestres espirituais da Idade Média Central. Cônego Regular na Abadia "
    "de São Vítor em Paris, distinguiu-se pela síntese monumental entre erudição humanística, teologia bíblica e "
    "contemplação mística, sendo cognominado na tradição escolástica como «o segundo Agostinho» (*alter Augustinus*).",
    "[^ne2]: **Proveniência do Texto**: Esta edição em Markdown semântico foi compilada e revisada para o OpenSciMD "
    "e o leitor LeiaME a partir dos tratados traduzidos e digitalizados originalmente pelo portal *cristianismo.org.br*, "
    "sob licença de livre reprodução para fins de estudo e uso não comercial.",
    "[^ne3]: **Fixação Ortográfica e Tipográfica**: A grafia do texto foi fixada em conformidade com o Acordo Ortográfico "
    "da Língua Portuguesa vigente, preservando-se rigorosamente a integridade lexical, os termos latinos e as escolhas "
    "de tradução do texto-fonte, com normalização de citações bíblicas e aparatos críticos.",
)


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
    def _next_non_empty_starts_notes(cls, lines: list[str], start_idx: int) -> bool:
        for idx in range(start_idx, len(lines)):
            stripped = lines[idx].strip()
            if not stripped:
                continue
            return bool(
                re.match(r"^###\s+Notas\b", stripped, re.IGNORECASE)
                or re.match(r"^\[\^[a-zA-Z0-9_-]+\]:\s+", stripped)
            )
        return False

    @classmethod
    def extract_notes_from_body(cls, body: str) -> tuple[str, list[str]]:
        """Extrai declarações de notas de rodapé do pós-texto e retorna o corpo limpo e as notas."""
        lines = body.splitlines()
        clean_lines: list[str] = []
        collected_notes: list[str] = []
        in_notes_section = False

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "---" and not in_notes_section:
                if cls._next_non_empty_starts_notes(lines, idx + 1):
                    in_notes_section = True
                    continue
                clean_lines.append(line)
                continue

            if in_notes_section:
                if re.match(r"^\[\^[a-zA-Z0-9_-]+\]:\s+", stripped):
                    collected_notes.append(stripped)
                elif re.match(r"^###\s+Notas\b", stripped, re.IGNORECASE):
                    continue
                elif stripped and not stripped.startswith("#"):
                    if collected_notes:
                        collected_notes[-1] += f" {stripped}"
            else:
                if re.match(r"^\[\^[a-zA-Z0-9_-]+\]:\s+", stripped):
                    collected_notes.append(stripped)
                    in_notes_section = True
                else:
                    clean_lines.append(line)

        clean_body = "\n".join(clean_lines).strip()
        return clean_body, collected_notes

    @classmethod
    def _resolve_editorial_preset_notes(
        cls,
        metadata: dict[str, Any],
        add_default_editorial_notes: bool,
        preset: str | None,
        custom_editorial_notes: list[str] | None,
    ) -> list[str]:
        if custom_editorial_notes is not None:
            return list(custom_editorial_notes)
        if preset == "hugo-vitor":
            return list(_HUGO_VITOR_EDITORIAL_NOTES)
        if not add_default_editorial_notes:
            return []

        author_val = str(metadata.get("author") or "").lower()
        authors_val = metadata.get("authors") or []
        authors_str = " ".join(
            str(a.get("name", "")) if isinstance(a, dict) else str(a) for a in authors_val
        ).lower()
        if "hugo de são vítor" in author_val or "hugo de são vítor" in authors_str:
            return list(_HUGO_VITOR_EDITORIAL_NOTES)
        return []

    @classmethod
    def assemble_volume(
        cls,
        parts_dir: str | Path,
        output_path: str | Path,
        metadata: dict[str, Any],
        add_default_editorial_notes: bool = True,
        preset: str | None = None,
        editorial_notes: list[str] | None = None,
    ) -> Path:
        """Monta um volume a partir de arquivos Markdown ordenados em parts_dir."""
        parts_path = Path(parts_dir).resolve()
        out_file = Path(output_path).resolve()

        if not parts_path.exists() or not parts_path.is_dir():
            raise FileNotFoundError(f"Diretório de partes não encontrado: {parts_path}")

        part_files = sorted([f for f in parts_path.glob("*.md") if f.is_file()])
        if not part_files:
            raise ValueError(f"Nenhum arquivo Markdown encontrado em: {parts_path}")

        preset_notes = cls._resolve_editorial_preset_notes(
            metadata=metadata,
            add_default_editorial_notes=add_default_editorial_notes,
            preset=preset,
            custom_editorial_notes=editorial_notes,
        )
        header_anchors = "".join(
            m.group(1) for note in preset_notes if (m := re.match(r"^(\[\^[^\]]+\]):", note))
        )

        assembled_sections: list[str] = []
        all_notes: list[str] = []
        first_section = True

        for part_file in part_files:
            parsed = parse_markdown_file(str(part_file))
            part_meta = parsed.get("metadata", {})
            raw_body = str(parsed.get("body", "")).strip()

            clean_body, part_notes = cls.extract_notes_from_body(raw_body)
            all_notes.extend(part_notes)

            part_title = part_meta.get("title")
            if not part_title:
                first_h = re.search(r"^#+\s+(.*)$", clean_body, re.MULTILINE)
                if first_h:
                    part_title = first_h.group(1).strip()
                    clean_body = clean_body[first_h.end() :].strip()
                else:
                    part_title = part_file.stem

            clean_body = re.sub(r"^#\s+.*?\n", "", clean_body).strip()
            body_shifted = cls.shift_headings(clean_body, level_offset=1)

            if salopdoc is not None:
                try:
                    quote_conv = salopdoc.QuoteConverter()
                    body_shifted = quote_conv.convert(body_shifted)
                except Exception:
                    pass

            clean_title = str(part_title).strip("*_ ")
            if first_section and header_anchors:
                section_header = f"## *{clean_title}*{header_anchors}"
                first_section = False
            else:
                section_header = f"## *{clean_title}*"
                first_section = False

            assembled_sections.append(f"{section_header}\n\n{body_shifted}")

        full_body = "\n\n".join(assembled_sections).strip()

        collected_editorial: list[str] = list(preset_notes)
        translator_notes: list[str] = []
        author_notes: list[str] = []

        for note in all_notes:
            if note.startswith("[^ne"):
                if note not in collected_editorial:
                    collected_editorial.append(note)
            elif note.startswith("[^nt"):
                if note not in translator_notes:
                    translator_notes.append(note)
            else:
                if note not in author_notes:
                    author_notes.append(note)

        notes_blocks: list[str] = []
        if collected_editorial:
            notes_blocks.append("### Notas Editoriais\n\n" + "\n\n".join(collected_editorial))
        if translator_notes:
            notes_blocks.append("### Notas do Tradutor\n\n" + "\n\n".join(translator_notes))
        if author_notes:
            notes_blocks.append("### Notas do Autor\n\n" + "\n\n".join(author_notes))

        post_text = ""
        if notes_blocks:
            post_text = "\n\n---\n\n" + "\n\n".join(notes_blocks)

        is_hugo_preset = preset == "hugo-vitor" or bool(preset_notes and preset_notes == list(_HUGO_VITOR_EDITORIAL_NOTES))
        default_author_name = metadata.get("author") or ("Hugo de São Vítor" if is_hugo_preset else "Autor Desconhecido")
        default_authors = [{"name": default_author_name}]

        frontmatter_data: dict[str, Any] = {
            "title": metadata.get("title", "Obra sem Título"),
            "authors": metadata.get("authors", default_authors),
            "summary": metadata.get("summary", ""),
            "date": metadata.get("date", "c. 1130 d.C." if is_hugo_preset else ""),
            "license": metadata.get("license", "CC BY-NC 4.0"),
            "categories": metadata.get("categories", ["Teologia"]),
            "language": metadata.get("language", "pt-BR"),
        }
        translator_val = metadata.get("translator") or ("Equipe Editorial cristianismo.org.br" if is_hugo_preset else None)
        if translator_val:
            frontmatter_data["translator"] = translator_val
        if "originalLanguage" in metadata:
            frontmatter_data["originalLanguage"] = metadata["originalLanguage"]
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
        out_file.write_text(final_content, encoding="utf-8")
        return out_file
