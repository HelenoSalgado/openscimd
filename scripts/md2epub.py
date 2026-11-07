#!/usr/bin/env python3
"""Conversor Editorial de Markdown para EPUB 3 com metadados semânticos e folha de estilo clássica."""

import html
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from PIL import Image

_MESES_PT: Dict[int, str] = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def format_editorial_date(raw_date: Any) -> str:
    """Formata datas ISO/numéricas para o padrão editorial brasileiro por extenso e higieniza datas clássicas."""
    if raw_date is None:
        return ""

    if isinstance(raw_date, (datetime, date)):
        return f"{raw_date.day} de {_MESES_PT[raw_date.month]} de {raw_date.year}"

    text = str(raw_date).strip()
    if not text:
        return ""

    # 1. Padrão ISO: YYYY-MM-DD ou YYYY/MM/DD (com sufixo de hora opcional)
    m_iso = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[T\s].*)?$", text)
    if m_iso:
        year, month, day = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{day} de {_MESES_PT[month]} de {year}"

    # 2. Padrão numérico BR: DD-MM-YYYY ou DD/MM/YYYY
    m_br = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", text)
    if m_br:
        day, month, year = int(m_br.group(1)), int(m_br.group(2)), int(m_br.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{day} de {_MESES_PT[month]} de {year}"

    # 3. Ano e mês: YYYY-MM ou YYYY/MM
    m_ym = re.match(r"^(\d{4})[-/](\d{1,2})$", text)
    if m_ym:
        year, month = int(m_ym.group(1)), int(m_ym.group(2))
        if 1 <= month <= 12:
            return f"{_MESES_PT[month]} de {year}"

    # 4. Mês e ano: MM-YYYY ou MM/YYYY
    m_my = re.match(r"^(\d{1,2})[-/](\d{4})$", text)
    if m_my:
        month, year = int(m_my.group(1)), int(m_my.group(2))
        if 1 <= month <= 12:
            return f"{_MESES_PT[month]} de {year}"

    # 5. Datas históricas (normalizar '386 d.C' / '107 d. C.' -> '386 d.C.' / '107 d.C.')
    normalized = re.sub(r"\b([adAD])\.\s*[cC]\.?(?=$|\s|[,;)])", lambda m: f"{m.group(1).lower()}.C.", text)
    return normalized


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extrai metadados do YAML frontmatter e separa o corpo do Markdown."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        raw_yaml, body = match.groups()
        try:
            metadata = yaml.safe_load(raw_yaml) or {}
            if isinstance(metadata, dict):
                return metadata, body
            return {}, content
        except yaml.YAMLError:
            return {}, content
    return {}, content


def resolve_authors_list(metadata: Dict[str, Any], default: str = "Autor Desconhecido") -> List[str]:
    """Extrai a lista de nomes de autores a partir de 'author' ou 'authors' no frontmatter."""
    raw_author = metadata.get("author")
    names: List[str] = []

    if isinstance(raw_author, str) and raw_author.strip():
        names.append(raw_author.strip())
    elif isinstance(raw_author, list):
        for item in raw_author:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
            elif isinstance(item, dict) and str(item.get("name", "")).strip():
                names.append(str(item["name"]).strip())

    if not names:
        raw_authors = metadata.get("authors")
        if isinstance(raw_authors, list):
            for item in raw_authors:
                if isinstance(item, str) and item.strip():
                    names.append(item.strip())
                elif isinstance(item, dict) and str(item.get("name", "")).strip():
                    names.append(str(item["name"]).strip())
        elif isinstance(raw_authors, str) and raw_authors.strip():
            names.append(raw_authors.strip())

    return names if names else [default]


def resolve_author_name(metadata: Dict[str, Any], default: str = "Autor Desconhecido") -> str:
    """Resolve o nome consolidado de autoria para exibição editorial."""
    return ", ".join(resolve_authors_list(metadata, default=default))


def find_cover_image(book_path: Path, base_dir: Optional[Path] = None) -> Optional[Path]:
    """Localiza a arte de capa correspondente ao livro/artigo nos diretórios de assets."""
    if base_dir is None:
        base_dir = book_path.resolve().parents[2] if len(book_path.resolve().parents) >= 3 else Path.cwd()

    stem = book_path.stem
    candidates = [
        base_dir / "assets" / "covers" / "originals" / f"{stem}.png",
        base_dir / "assets" / "covers" / "originals" / f"{stem}.jpg",
        base_dir / "assets" / "covers" / "originals" / f"{stem}.jpeg",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.png",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.jpg",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.jpeg",
        base_dir / "assets" / "covers" / "originals" / f"{stem}.webp",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.webp",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def get_default_css_path(base_dir: Optional[Path] = None) -> Optional[Path]:
    """Retorna o caminho da folha de estilo editorial padrão para EPUB."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    css_candidate = base_dir / "scripts" / "templates" / "epub.css"
    if css_candidate.exists():
        return css_candidate
    return None


def _ensure_epub_compatible_image(
    image_path: Path,
    temp_dir: Path,
    project_root: Optional[Path] = None,
) -> Path:
    """Garante que a imagem esteja em um Core Media Type EPUB 3 (PNG/JPEG/GIF/SVG).

    Se a imagem for WebP, busca primeiro um original homônimo em PNG/JPEG e,
    caso não exista, converte para PNG no diretório temporário da compilação.
    """
    core_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
    if image_path.suffix.lower() in core_exts:
        return image_path

    if project_root is not None:
        stem = image_path.stem
        fallback_dirs = [
            project_root / "assets" / "images" / "originals",
            project_root / "assets" / "images",
            project_root / "assets" / "covers" / "originals",
        ]
        for folder in fallback_dirs:
            for ext in (".png", ".jpg", ".jpeg"):
                candidate = folder / f"{stem}{ext}"
                if candidate.exists() and candidate.is_file():
                    return candidate

    converted_path = temp_dir / f"{image_path.stem}.png"
    counter = 1
    while converted_path.exists():
        converted_path = temp_dir / f"{image_path.stem}_{counter}.png"
        counter += 1

    with Image.open(image_path) as img:
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img.save(converted_path, format="PNG")

    return converted_path


def _resolve_markdown_images(
    body: str,
    input_dir: Path,
    project_root: Path,
    temp_dir: Path,
) -> str:
    """Resolve caminhos de imagens locais/web (/assets/...) e converte WebP para PNG."""
    pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def _replace(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        raw_inner = match.group(2).strip()

        # Separar eventual título opcional entre aspas: ![alt](caminho "título")
        title_part = ""
        url_part = raw_inner
        title_match = re.match(r'^(\S+)\s+(".*"|\'.*\')$', raw_inner)
        if title_match:
            url_part = title_match.group(1)
            title_part = f" {title_match.group(2)}"

        if url_part.startswith(("http://", "https://", "data:")):
            return match.group(0)

        candidates: List[Path] = []
        if url_part.startswith("/"):
            rel = url_part.lstrip("/")
            candidates.append(project_root / rel)
            stem_name = Path(rel).name
            candidates.append(project_root / "assets" / "images" / "originals" / stem_name)
            candidates.append(project_root / "assets" / "images" / "desktop" / stem_name)
            candidates.append(project_root / "assets" / "desktop" / stem_name)
        else:
            candidates.append((input_dir / url_part).resolve())
            candidates.append((project_root / url_part).resolve())

        resolved_img: Optional[Path] = None
        for cand in candidates:
            if cand.exists() and cand.is_file():
                resolved_img = cand
                break

        if resolved_img is None:
            return match.group(0)

        compatible_img = _ensure_epub_compatible_image(resolved_img, temp_dir, project_root)
        return f"![{alt_text}]({compatible_img.as_posix()}{title_part})"

    return pattern.sub(_replace, body)


def strip_empty_footnote_sections(body: str) -> str:
    """Remove cabeçalhos de seções de notas (e divisores precedentes) que contêm apenas definições [^id]:."""
    lines = body.splitlines()
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    notes_title_re = re.compile(
        r"^\*?_?Notas?\b",
        re.IGNORECASE,
    )
    footnote_def_re = re.compile(r"^\[\^[^\]]+\]:")

    # Identificar intervalos entre cabeçalhos (ignorando blocos de código cercados)
    in_fence = False
    heading_indices: List[int] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence and heading_re.match(line):
            heading_indices.append(idx)

    lines_to_remove: set[int] = set()

    for pos, h_idx in enumerate(heading_indices):
        h_match = heading_re.match(lines[h_idx])
        if not h_match:
            continue
        h_title = h_match.group(2).strip()
        if not notes_title_re.match(h_title):
            continue

        end_idx = heading_indices[pos + 1] if pos + 1 < len(heading_indices) else len(lines)
        section_lines = lines[h_idx + 1 : end_idx]

        # Verificar se o conteúdo da seção consiste exclusivamente em definições de notas [^...]:
        # (incluindo eventuais linhas de continuação e divisores ---)
        has_footnote_def = False
        has_regular_prose = False
        in_current_footnote = False

        for s_line in section_lines:
            s_stripped = s_line.strip()
            if not s_stripped:
                continue
            if s_stripped == "---":
                in_current_footnote = False
                continue
            if footnote_def_re.match(s_stripped):
                has_footnote_def = True
                in_current_footnote = True
            elif in_current_footnote:
                # Linha de continuação da nota atual
                continue
            else:
                has_regular_prose = True
                break

        if has_footnote_def and not has_regular_prose:
            lines_to_remove.add(h_idx)
            # Remover também divisor '---' imediatamente anterior ao cabeçalho de notas
            prev_idx = h_idx - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0 and lines[prev_idx].strip() == "---":
                lines_to_remove.add(prev_idx)
        elif not has_footnote_def and not has_regular_prose:
            # Cabeçalho de notas completamente vazio no final
            lines_to_remove.add(h_idx)
            prev_idx = h_idx - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0 and lines[prev_idx].strip() == "---":
                lines_to_remove.add(prev_idx)

    filtered_lines = [line for idx, line in enumerate(lines) if idx not in lines_to_remove]

    # Remover divisores '---' órfãos no extremo final do documento (após notas ou texto)
    # preservando as definições de notas de rodapé.
    # Se a última linha não-vazia do arquivo for '---', removê-la.
    while filtered_lines and not filtered_lines[-1].strip():
        filtered_lines.pop()
    while filtered_lines and filtered_lines[-1].strip() == "---":
        filtered_lines.pop()
        while filtered_lines and not filtered_lines[-1].strip():
            filtered_lines.pop()

    # Também remover '---' órfão que tenha ficado imediatamente antes de um bloco final puro de [^id]:
    last_prose_idx = -1
    for idx, line in enumerate(filtered_lines):
        s = line.strip()
        if not s or footnote_def_re.match(s):
            continue
        last_prose_idx = idx
    if last_prose_idx >= 0 and filtered_lines[last_prose_idx].strip() == "---":
        # Verificar se após last_prose_idx só há linhas vazias ou definições de notas
        tail = [l.strip() for l in filtered_lines[last_prose_idx + 1 :] if l.strip()]
        if all(footnote_def_re.match(t) for t in tail):
            filtered_lines.pop(last_prose_idx)

    return "\n".join(filtered_lines)


def normalize_github_alerts(body: str) -> str:
    """Converte marcadores GitHub Alert (> [!NOTE], etc.) em rótulos editoriais limpos."""
    labels = {
        "NOTE": "Nota",
        "TIP": "Dica",
        "IMPORTANT": "Importante",
        "WARNING": "Atenção",
        "CAUTION": "Cuidado",
    }
    lines = body.splitlines()
    out: List[str] = []
    alert_re = re.compile(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", re.IGNORECASE)

    i = 0
    while i < len(lines):
        m = alert_re.match(lines[i])
        if m:
            kind = m.group(1).upper()
            rest = m.group(2).strip()
            label = labels.get(kind, "Nota")
            if rest:
                out.append(f"> **{label}:** {rest}")
            elif i + 1 < len(lines) and lines[i + 1].lstrip().startswith(">"):
                next_content = re.sub(r"^>\s?", "", lines[i + 1].lstrip())
                out.append(f"> **{label}:** {next_content}")
                i += 2
                continue
            else:
                out.append(f"> **{label}**")
        else:
            out.append(lines[i])
        i += 1

    return "\n".join(out)


def separate_consecutive_verses(body: str) -> str:
    """Separa versículos consecutivos iniciados por dígitos sobrescritos em parágrafos individuais."""
    verse_re = re.compile(r"^[¹²³⁴⁵⁶⁷⁸⁹⁰]+\s+\S")
    lines = body.splitlines()
    result: List[str] = []

    for idx, line in enumerate(lines):
        if idx > 0 and verse_re.match(line.strip()) and verse_re.match(lines[idx - 1].strip()):
            result.append("")
        result.append(line)

    return "\n".join(result)


def _normalize_title_for_comparison(text: str) -> str:
    """Normaliza título removendo formatação Markdown, notas e pontuação para comparação."""
    cleaned = re.sub(r"\[\^[^\]]+\]", "", text)
    cleaned = re.sub(r"[*_`~]", "", cleaned)
    cleaned = re.sub(r"[^\w\s]", "", cleaned, flags=re.UNICODE)
    return " ".join(cleaned.lower().split())


def normalize_headings_and_preamble(body: str, doc_title: str) -> Tuple[str, bool, str]:
    """Normaliza a hierarquia de cabeçalhos e protege o preâmbulo contra fusão na Ficha Catalográfica.

    Retorna:
        (corpo_normalizado, shift_heading, heading_prefix)
    """
    lines = body.strip().splitlines()
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    footnote_def_re = re.compile(r"^\[\^[^\]]+\]:")

    def _collect_headings(src_lines: List[str]) -> List[Tuple[int, int, str]]:
        collected: List[Tuple[int, int, str]] = []
        in_fence = False
        for idx, ln in enumerate(src_lines):
            if ln.strip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if not in_fence:
                m = heading_re.match(ln)
                if m:
                    collected.append((idx, len(m.group(1)), m.group(2).strip()))
        return collected

    headings = _collect_headings(lines)
    norm_doc_title = _normalize_title_for_comparison(doc_title)

    # 1. Tratar H1 único inicial quando o restante do documento utiliza H2 como capítulos
    h1_list = [h for h in headings if h[1] == 1]
    h2_list = [h for h in headings if h[1] == 2]
    if len(h1_list) == 1 and headings and headings[0][1] == 1 and len(h2_list) >= 1:
        first_idx, _, first_text = headings[0]
        second_idx = headings[1][0]
        between_lines = [ln.strip() for ln in lines[first_idx + 1 : second_idx] if ln.strip()]
        norm_first = _normalize_title_for_comparison(first_text)

        is_title_repeat = bool(
            norm_doc_title
            and norm_first
            and (norm_first == norm_doc_title or norm_first.startswith(norm_doc_title) or norm_doc_title.startswith(norm_first))
        )

        if is_title_repeat and not between_lines:
            # Ex.: '# Poética' imediatamente seguido de '## I' -> remover título duplicado
            lines.pop(first_idx)
        elif is_title_repeat and between_lines:
            # Ex.: Folha de rosto histórica com subtítulo antes de '## Dedicatória'
            lines[first_idx] = f"## {first_text} {{.unnumbered .unlisted}}"
        else:
            # Ex.: '# Introdução' seguido de '## I. ...' -> alinhar nível com os demais capítulos
            lines[first_idx] = f"## {first_text}"

        headings = _collect_headings(lines)

    # 2. Caso o documento não tenha nenhum cabeçalho ou o menor nível seja >= 3
    if not headings or min(h[1] for h in headings) >= 3:
        lines = [f"## {doc_title}", ""] + lines
        headings = _collect_headings(lines)

    # 3. Corrigir saltos de hierarquia (ex.: H1 direto para H3 sem nenhum H2, como em Solilóquios)
    levels_present = sorted({h[1] for h in headings})
    if 1 in levels_present and 2 not in levels_present and any(lv >= 3 for lv in levels_present):
        gap = min(lv for lv in levels_present if lv >= 3) - 2
        in_fence = False
        for idx, ln in enumerate(lines):
            if ln.strip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if not in_fence:
                m = heading_re.match(ln)
                if m and len(m.group(1)) >= 3:
                    new_level = max(2, len(m.group(1)) - gap)
                    lines[idx] = f"{'#' * new_level} {m.group(2)}"
        headings = _collect_headings(lines)

    min_level = min(h[1] for h in headings) if headings else 2
    shift_heading = min_level == 2
    heading_prefix = "##" if shift_heading else "#"

    # 4. Proteger eventual preâmbulo antes do primeiro cabeçalho de nível topo
    first_top_idx = next((h[0] for h in headings if h[1] == min_level), 0)
    if first_top_idx > 0:
        preamble_non_empty = [
            ln.strip()
            for ln in lines[:first_top_idx]
            if ln.strip() and not footnote_def_re.match(ln.strip())
        ]
        if preamble_non_empty:
            # Verificar se o preâmbulo é apenas elemento paratextual (imagem, citação/nota, divisor)
            is_paratext_only = all(
                ln.startswith(("![", ">", "---", "<")) for ln in preamble_non_empty
            )
            if is_paratext_only:
                lines = [f"{heading_prefix} {{.unnumbered .unlisted}}", ""] + lines
            else:
                existing_titles = {_normalize_title_for_comparison(h[2]) for h in headings}
                intro_label = "Introdução" if "introducao" not in existing_titles and "introdução" not in existing_titles else "Preâmbulo"
                lines = [f"{heading_prefix} {intro_label}", ""] + lines

    return "\n".join(lines).strip(), shift_heading, heading_prefix


def generate_frontmatter_editorial_blocks(metadata: Dict[str, Any], prefix: str = "##") -> str:
    """Gera blocos pré-textuais editoriais: Folha de Rosto e Ficha Catalográfica."""
    title = str(metadata.get("title", "Obra")).strip()
    author = resolve_author_name(metadata, default="Autor Desconhecido")
    translator = metadata.get("translator")
    publisher = str(metadata.get("publisher", "OpenSciMD")).strip()
    year = datetime.now().year
    license_ = str(metadata.get("license", "Domínio Público")).strip().rstrip(".")
    formatted_date = format_editorial_date(metadata.get("date", ""))
    date_for_cip = formatted_date.rstrip(".")
    categories = metadata.get("categories", ["Filosofia"])
    cat_str = (", ".join(str(c) for c in categories) if isinstance(categories, list) else str(categories)).strip().rstrip(".")

    blocks = [
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="editorial-titlepage">',
        f'<div class="main-title">{html.escape(title)}</div>',
    ]

    if formatted_date:
        is_modern_full_date = any(f" de {m} de " in formatted_date or formatted_date.startswith(f"{m} de ") for m in _MESES_PT.values())
        subtitle_label = formatted_date if is_modern_full_date else f"Composição canônica: {formatted_date}"
        blocks.append(f'<div class="sub-title">{html.escape(subtitle_label)}</div>')

    blocks.append(f'<div class="author-name">{html.escape(author)}</div>')

    if translator:
        blocks.append(f'<div class="translator-info">Traduzido por {html.escape(str(translator).strip())}</div>')

    cip_translator = f" ; tradução de {html.escape(str(translator).strip())}" if translator else ""
    blocks.extend([
        "</div>\n",
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="catalographic-wrapper">',
        '<div class="catalographic-box">',
        "<h4>Dados Internacionais de Catalogação na Publicação (CIP)</h4>",
        f"<p><strong>{html.escape(author)}</strong></p>",
        f"<p><em>{html.escape(title)}</em> / {html.escape(author)}{cip_translator}. — {html.escape(publisher)}, {year}.</p>",
    ])

    if date_for_cip:
        blocks.append(f"<p>Datação original da obra: {html.escape(date_for_cip)}.</p>")

    blocks.extend([
        f"<p>Assunto(s): {html.escape(cat_str)}.</p>",
        f"<p>Licença Editorial: {html.escape(license_)}.</p>",
        "<p>Publicação digital aberta de livre difusão cultural e científica.</p>",
        "</div>\n",
        "</div>\n",
    ])

    return "\n".join(blocks)


def generate_colophon_markdown(metadata: Dict[str, Any], prefix: str = "##") -> str:
    """Gera bloco editorial final (colofão) com dados do selo OpenSciMD e tradução."""
    title = str(metadata.get("title", "Obra")).strip()
    author = resolve_author_name(metadata, default="Autor Desconhecido")
    translator = metadata.get("translator")
    publisher = str(metadata.get("publisher", "OpenSciMD")).strip()
    license_ = str(metadata.get("license", "Domínio Público")).strip().rstrip(".")
    year = datetime.now().year

    colophon = [
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="colophon-box">',
        f"<h4>{html.escape(publisher)} · Edições Abertas</h4>",
        f"<p><strong>{html.escape(title)}</strong> — {html.escape(author)}</p>",
    ]

    if translator:
        colophon.append(f"<p>Traduzido por {html.escape(str(translator).strip())}</p>")

    colophon.extend([
        f"<p><em>Licença Editorial:</em> {html.escape(license_)}</p>",
        "<p>Projeto OpenSciMD: Difusão científica, literária e filosófica em formatos abertos.</p>",
        "<p>Composto digitalmente em tipos clássicos Garamond.</p>",
        f"<small>© {year} {html.escape(publisher)} · Livro Digital EPUB 3</small>",
        "</div>\n",
    ])

    return "\n".join(colophon)


def generate_institutional_page(prefix: str = "##") -> str:
    """Gera página institucional final apresentando OpenSciMD, Leia-me e citação acadêmica."""
    blocks = [
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="institutional-wrapper">',
        '<div class="institutional-card">',
        '<div class="institutional-badge">OpenSciMD &amp; Leia-me</div>',
        "<h3>Conhecimento Aberto, Leitura Ativa</h3>",
        '<p class="institutional-lead">',
        "Esta edição digital foi produzida pelo <strong>OpenSciMD</strong>, uma iniciativa voltada à curadoria, normalização semântica e preservação de tratados clássicos e artigos acadêmicos em formatos digitais abertos e acessíveis.",
        "</p>",
        '<div class="institutional-section">',
        "<h4>Aplicativo Oficial Leia-me</h4>",
        "<p>",
        "Para uma experiência aprofundada de estudo e pesquisa, utilize o aplicativo <strong>Leia-me</strong>. Desenvolvido para o público estudantil e acadêmico, o app oferece:",
        "</p>",
        "<ul>",
        "<li>Leitura imersiva em Markdown e navegação por sumário interativo;</li>",
        "<li>Busca aprofundada (FTS) com suporte a termos gregos, latinos e notas;</li>",
        "<li>Caderno de anotações e realces coloridos vinculados aos trechos;</li>",
        "<li>Acesso completo e leitura 100% offline no seu dispositivo;</li>",
        "<li>Dicionário da Língua Portuguesa integrado.</li>",
        "</ul>",
        '<p class="institutional-link-box">',
        'Conheça: <a href="https://leiame.app">leiame.app</a>',
        "</p>",
        "</div>",
        '<div class="institutional-section">',
        "<h4>Licença Editorial e Como Citar</h4>",
        "<p>",
        "A compilação editorial, normalização tipográfica e identidade gráfica desta edição estão protegidas sob a licença <strong>Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)</strong>.",
        "</p>",
        "<p>",
        "Você é livre para baixar, armazenar e compartilhar esta edição sem finalidade comercial e preservando a integridade original. Para fins de pesquisa, referência acadêmica ou redistribuição, cite a compilação:",
        "</p>",
        '<p class="citation-box">',
        "<code>Salgado, H. (2026). OpenSciMD: Open-Access Scientific Articles in Markdown (Version 1.1.0) [Data set]. https://github.com/HelenoSalgado/openscimd</code>",
        "</p>",
        '<p class="institutional-repo">',
        'Repositório: <a href="https://github.com/HelenoSalgado/openscimd">github.com/HelenoSalgado/openscimd</a>',
        "</p>",
        "</div>",
        "</div>\n",
        "</div>\n",
    ]
    return "\n".join(blocks)


def _extract_plain_h1_text(xhtml_text: str) -> Optional[str]:
    """Extrai o texto puro do primeiro elemento <h1> não vazio de um XHTML."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", xhtml_text, flags=re.DOTALL)
    if not m:
        return None
    inner = re.sub(r"<a[^>]*class=\"footnote-ref\"[^>]*>.*?</a>", "", m.group(1), flags=re.DOTALL)
    plain = re.sub(r"<[^>]+>", "", inner)
    plain = html.unescape(" ".join(plain.split())).strip()
    return plain if plain else None


def _clean_epub_container(epub_path: Path, book_title: str = "Obra") -> None:
    """Higieniza documentos XHTML, títulos de capítulos, estilos vazios e landmarks do EPUB."""
    temp_epub = epub_path.with_suffix(".tmp.epub")
    escaped_book_title = html.escape(book_title)

    with zipfile.ZipFile(epub_path, "r") as z_in, zipfile.ZipFile(
        temp_epub, "w", compression=zipfile.ZIP_DEFLATED
    ) as z_out:
        # Garantir que 'mimetype' seja sempre o primeiro item e sem compressão (ZIP_STORED)
        items = z_in.infolist()
        items_sorted = sorted(items, key=lambda info: 0 if info.filename == "mimetype" else 1)

        for item in items_sorted:
            data = z_in.read(item.filename)

            if item.filename.endswith(".xhtml"):
                text = data.decode("utf-8")

                # 1. Remover tags <style> vazias geradas pelo Pandoc
                text = re.sub(r"\s*<style>\s*</style>", "", text)

                # 1b. Garantir semântica <sup> dentro das referências de notas (<a class="footnote-ref">)
                text = re.sub(
                    r'(<a\b[^>]*\bclass="footnote-ref"[^>]*>)(?!\s*<sup\b)(.*?)(</a>)',
                    r"\1<sup>\2</sup>\3",
                    text,
                )

                # 2. Remover <h1> vazios de seções unnumbered/unlisted (pré/pós-textuais e frontispício)
                if (
                    "editorial-titlepage" in text
                    or "catalographic-box" in text
                    or "colophon-box" in text
                    or "institutional-card" in text
                ):
                    text = re.sub(r'<h1 class="unnumbered[^"]*">\s*</h1>\s*', "", text, flags=re.DOTALL)
                else:
                    text = re.sub(r'<h1 class="unnumbered unlisted">\s*</h1>\s*', "", text)

                # 3. Substituir <title>chXXX.xhtml</title> por título semântico real
                semantic_title = escaped_book_title
                if "editorial-titlepage" in text:
                    semantic_title = f"{escaped_book_title} — Folha de Rosto"
                elif "catalographic-box" in text:
                    semantic_title = "Ficha Catalográfica"
                elif "colophon-box" in text:
                    semantic_title = "Colofão"
                elif "institutional-card" in text:
                    semantic_title = "Sobre esta Edição — OpenSciMD"
                else:
                    h1_plain = _extract_plain_h1_text(text)
                    if h1_plain:
                        semantic_title = html.escape(h1_plain)

                text = re.sub(
                    r"<title>ch\d+\.xhtml</title>",
                    f"<title>{semantic_title}</title>",
                    text,
                )

                # 4. Localizar landmarks e título em português no nav.xhtml (sem repetir o título da obra)
                if item.filename.endswith("nav.xhtml"):
                    text = re.sub(r"<title>.*?</title>", "<title>Sumário</title>", text, flags=re.DOTALL)
                    text = text.replace(">Cover</a>", ">Capa</a>")
                    text = text.replace(">Table of Contents</a>", ">Sumário</a>")

                data = text.encode("utf-8")

            elif item.filename.endswith(".opf"):
                opf_text = data.decode("utf-8")
                opf_text = opf_text.replace('title="Cover"', 'title="Capa"')
                data = opf_text.encode("utf-8")

            if item.filename == "mimetype":
                mime_info = zipfile.ZipInfo("mimetype", date_time=item.date_time)
                mime_info.compress_type = zipfile.ZIP_STORED
                z_out.writestr(mime_info, data, compress_type=zipfile.ZIP_STORED)
            else:
                out_info = zipfile.ZipInfo(item.filename, date_time=item.date_time)
                out_info.compress_type = zipfile.ZIP_DEFLATED
                out_info.external_attr = item.external_attr
                z_out.writestr(out_info, data, compress_type=zipfile.ZIP_DEFLATED)

    temp_epub.replace(epub_path)


def resolve_epub_output_path(
    input_md_path: Path,
    project_root: Path,
    output_epub_path: Optional[str | Path] = None,
    structured: bool = True,
) -> Path:
    """Resolve o caminho de saída para o EPUB, preservando a hierarquia de content/ se estruturado."""
    if output_epub_path:
        return Path(output_epub_path).resolve()

    content_dir = (project_root / "content").resolve()
    resolved_input = input_md_path.resolve()

    if structured:
        if resolved_input.is_relative_to(content_dir):
            rel = resolved_input.relative_to(content_dir)
            return project_root / "dist" / "content" / rel.with_suffix(".epub")
        parts = resolved_input.parts
        if "content" in parts:
            idx = parts.index("content")
            rel = Path(*parts[idx + 1 :])
            return project_root / "dist" / "content" / rel.with_suffix(".epub")

    return project_root / "dist" / f"{resolved_input.stem}.epub"


def convert_md_to_epub(
    input_md_path: str | Path,
    output_epub_path: Optional[str | Path] = None,
    cover_path: Optional[str | Path] = None,
    css_path: Optional[str | Path] = None,
    base_dir: Optional[str | Path] = None,
    add_colophon: bool = False,
    add_editorial_pages: bool = True,
    add_institutional_page: bool = True,
    structured: bool = True,
) -> Path:
    """Converte um documento Markdown para formato EPUB 3 profissional com Pandoc."""
    input_path = Path(input_md_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {input_path}")

    project_root = Path(base_dir).resolve() if base_dir else input_path.parent
    while project_root != project_root.parent and not (project_root / "pyproject.toml").exists():
        project_root = project_root.parent

    out_path = resolve_epub_output_path(
        input_md_path=input_path,
        project_root=project_root,
        output_epub_path=output_epub_path,
        structured=structured,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which("pandoc"):
        raise RuntimeError("O executável 'pandoc' não foi encontrado no sistema operacional.")

    content = input_path.read_text(encoding="utf-8")
    metadata, body = extract_frontmatter(content)

    # Resolver metadados essenciais
    title = str(metadata.get("title", input_path.stem.replace("-", " ").title())).strip()
    authors_list = resolve_authors_list(metadata, default="OpenSciMD")
    translator = metadata.get("translator")
    lang = str(metadata.get("language", "pt-BR")).strip()
    summary = str(metadata.get("summary", "")).strip()
    rights = str(metadata.get("license", "Domínio Público")).strip()

    # Localizar capa se não fornecida
    resolved_cover: Optional[Path] = None
    if cover_path:
        resolved_cover = Path(cover_path).resolve()
        if not resolved_cover.exists():
            raise FileNotFoundError(f"Arquivo de capa não encontrado: {cover_path}")
    else:
        resolved_cover = find_cover_image(input_path, project_root)

    # Localizar folha de estilo
    resolved_css: Optional[Path] = None
    if css_path:
        resolved_css = Path(css_path).resolve()
    else:
        resolved_css = get_default_css_path(project_root)

    with tempfile.TemporaryDirectory(prefix="openscimd_epub_") as tmp_dir_str:
        temp_dir = Path(tmp_dir_str)

        # 1. Higienização estrutural e tipográfica do corpo Markdown
        clean_body = strip_empty_footnote_sections(body)
        clean_body = normalize_github_alerts(clean_body)
        clean_body = separate_consecutive_verses(clean_body)
        clean_body = _resolve_markdown_images(
            clean_body,
            input_dir=input_path.parent,
            project_root=project_root,
            temp_dir=temp_dir,
        )
        clean_body, shift_heading, heading_prefix = normalize_headings_and_preamble(
            clean_body, doc_title=title
        )

        # 2. Montar corpo editorial ordenado
        markdown_parts: List[str] = []

        if add_editorial_pages:
            editorial_pre = generate_frontmatter_editorial_blocks(metadata, prefix=heading_prefix)
            markdown_parts.append(editorial_pre)

        markdown_parts.append(clean_body)

        if add_colophon:
            colophon_md = generate_colophon_markdown(metadata, prefix=heading_prefix)
            markdown_parts.append(colophon_md)

        if add_institutional_page:
            institutional_md = generate_institutional_page(prefix=heading_prefix)
            markdown_parts.append(institutional_md)

        compiled_markdown = "\n\n".join(markdown_parts)
        tmp_md_path = temp_dir / "compiled_book.md"
        tmp_md_path.write_text(compiled_markdown, encoding="utf-8")

        resource_paths = f"{input_path.parent.as_posix()}:{project_root.as_posix()}:{temp_dir.as_posix()}"

        cmd = [
            "pandoc",
            str(tmp_md_path),
            "-o",
            str(out_path),
            "-t",
            "epub3",
            "--epub-title-page=false",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            f"--resource-path={resource_paths}",
            f"--metadata=title:{title}",
            "--metadata=toc-title:Sumário",
            f"--metadata=lang:{lang}",
            "--metadata=publisher:OpenSciMD",
        ]

        for author_item in authors_list:
            cmd.append(f"--metadata=author:{author_item}")

        if shift_heading:
            cmd.append("--shift-heading-level-by=-1")

        if translator:
            cmd.append(f"--metadata=contributor:{str(translator).strip()} (Tradutor)")

        if summary:
            cmd.append(f"--metadata=description:{summary}")

        if rights:
            cmd.append(f"--metadata=rights:{rights}")

        if resolved_css and resolved_css.exists():
            cmd.append(f"--css={resolved_css}")

        if resolved_cover and resolved_cover.exists():
            epub_cover = _ensure_epub_compatible_image(resolved_cover, temp_dir, project_root)
            cmd.append(f"--epub-cover-image={epub_cover}")

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Erro ao executar pandoc: {proc.stderr.strip()}")

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Falha ao gerar arquivo EPUB em {out_path}")

    # Higienizar container EPUB (títulos semânticos, landmarks e remoção de tags vazias)
    _clean_epub_container(out_path, book_title=title)

    return out_path


def batch_convert_content(
    base_dir: Optional[str | Path] = None,
    target_type: str = "all",
    cover_path: Optional[str | Path] = None,
    css_path: Optional[str | Path] = None,
    add_colophon: bool = False,
    add_editorial_pages: bool = True,
    add_institutional_page: bool = True,
) -> Dict[str, Any]:
    """Compila em lote todos os livros e artigos presentes em content/ para dist/content/."""
    project_root = Path(base_dir).resolve() if base_dir else Path.cwd()
    while project_root != project_root.parent and not (project_root / "pyproject.toml").exists():
        project_root = project_root.parent

    content_dir = project_root / "content"
    if not content_dir.exists():
        raise FileNotFoundError(f"Diretório content não encontrado em: {content_dir}")

    targets: List[Path] = []
    if target_type in ("all", "books"):
        books_dir = content_dir / "books"
        if books_dir.exists():
            targets.extend(sorted([p for p in books_dir.rglob("*.md") if not p.name.startswith((".", "_"))]))

    if target_type in ("all", "articles"):
        articles_dir = content_dir / "articles"
        if articles_dir.exists():
            targets.extend(sorted([p for p in articles_dir.rglob("*.md") if not p.name.startswith((".", "_"))]))

    results: Dict[str, Any] = {
        "total": len(targets),
        "succeeded": [],
        "failed": [],
    }

    for md_file in targets:
        try:
            epub_file = convert_md_to_epub(
                input_md_path=md_file,
                cover_path=cover_path,
                css_path=css_path,
                base_dir=project_root,
                add_colophon=add_colophon,
                add_editorial_pages=add_editorial_pages,
                add_institutional_page=add_institutional_page,
                structured=True,
            )
            results["succeeded"].append({
                "source": md_file,
                "output": epub_file,
                "size_kb": round(epub_file.stat().st_size / 1024, 1),
            })
        except Exception as e:
            results["failed"].append({
                "source": md_file,
                "error": str(e),
            })

    return results
