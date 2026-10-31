"""
covers.py — Sistema de composição editorial de capas do OpenSciMD.

Estilo visual:
  - Ilustração de fundo artística ocupando 100% da área da capa (full bleed: 1696×2528 px).
  - Tipografia editorial clássica (Cormorant Garamond) sobreposta diretamente à arte.
  - Título em ouro fosco nobre (#E2C974 / #D4A847), subtítulo e autor em branco com sombreamento suave para legibilidade e elegância.
  - Data (quando aplicável) centralizada na base da capa.

Resolução canônica:
  1696 × 2528 px (proporção ~ 2:3).
Saídas responsivas (WebP):
  - desktop: 1696 px de largura
  - tablet:  1200 px de largura
  - mobile:  1080 px de largura
"""

import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scripts.utils import parse_markdown_file

# ── Resolução canônica ─────────────────────────────────────────────────────────
CANVAS_W = 1696
CANVAS_H = 2528
TARGET_DPI = (72, 72)

# ── Paleta de cores ───────────────────────────────────────────────────────────
COLOR_TITLE    = (226, 201, 116, 255)  # Matte Gold (#E2C974)
COLOR_SUBTITLE = (255, 255, 255, 255)  # Crisp White (#FFFFFF)
COLOR_AUTHOR   = (248, 250, 252, 255)  # Soft White (#F8FAFC)
COLOR_DATE     = (203, 213, 225, 240)  # Muted Slate (#CBD5E1)
COLOR_SHADOW   = (0, 0, 0, 220)        # Sombra suave

# ── Tamanhos de fonte de referência ───────────────────────────────────────────
TITLE_FONT_MAX = 175
TITLE_FONT_MIN = 72

# ── Tamanhos de saída por tela ─────────────────────────────────────────────────
SCREEN_SIZES = {
    "mobile" : 1080,
    "tablet" : 1200,
    "desktop": 1696,
}

# ── Caminhos de fonte (Cormorant Garamond, com fallbacks do sistema) ──────────
FONT_DIR = Path("/usr/share/fonts/TTF")

FONTS = {
    "bold"     : FONT_DIR / "CormorantGaramond-Bold.ttf",
    "semibold" : FONT_DIR / "CormorantGaramond-SemiBold.ttf",
    "regular"  : FONT_DIR / "CormorantGaramond-Regular.ttf",
}

FONT_FALLBACKS = {
    "bold"     : ["/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf"],
    "semibold" : ["/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf"],
    "regular"  : ["/usr/share/fonts/gsfonts/NimbusRoman-Regular.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf"],
}


# ══════════════════════════════════════════════════════════════════════════════
# Utilitários de Fonte
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_font(style: str) -> str:
    """Retorna o caminho da fonte Cormorant ou o melhor fallback disponível."""
    primary = FONTS.get(style)
    if primary and primary.exists():
        return str(primary)
    for path in FONT_FALLBACKS.get(style, []):
        if Path(path).exists():
            return path
    for f in Path("/usr/share/fonts").rglob("*.ttf"):
        name = f.name.lower()
        if style in ("bold", "semibold") and "bold" in name:
            return str(f)
        if style == "regular" and "regular" in name:
            return str(f)
    return None


def _load_font(style: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _resolve_font(style)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════════════════
# Utilitários de Texto
# ══════════════════════════════════════════════════════════════════════════════

def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_height(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Quebra `text` em linhas que cabem em `max_width` px."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _fit_font_to_zone(
    draw: ImageDraw.ImageDraw,
    text: str,
    style: str,
    max_width: int,
    available_height: int,
    font_max: int,
    font_min: int,
    line_spacing_factor: float = 1.22,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """
    Reduz o tamanho da fonte até que o texto caiba em `available_height`.
    Retorna (font, lines, font_size).
    """
    size = font_max
    while size >= font_min:
        font = _load_font(style, size)
        lines = _wrap_to_width(draw, text, font, max_width)
        line_h = int(size * line_spacing_factor)
        total_h = line_h * len(lines)
        if total_h <= available_height:
            return font, lines, size
        size -= 4
    font = _load_font(style, font_min)
    lines = _wrap_to_width(draw, text, font, max_width)
    return font, lines, font_min


# ══════════════════════════════════════════════════════════════════════════════
# Formatação de Datas
# ══════════════════════════════════════════════════════════════════════════════

_MONTHS_BR = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

_HISTORICAL_ERA = re.compile(
    r"^"
    r"(?P<prefix>c\.|ca\.|aprox\.)?\s*"
    r"(?P<year>\d{1,4})"
    r"\s*"
    r"(?P<era>a\.?\s*C\.?|d\.?\s*C\.?)?"
    r"$",
    re.IGNORECASE,
)

_MODERN_DATE_PATTERNS = [
    re.compile(r"^(?P<d>\d{1,2})[-/](?P<m>\d{1,2})[-/](?P<y>\d{4})$"),
    re.compile(r"^(?P<y>\d{4})[-/](?P<m>\d{1,2})[-/](?P<d>\d{1,2})$"),
    re.compile(r"^(?P<m>\d{1,2})[-/](?P<y>\d{4})$"),
    re.compile(r"^(?P<y>\d{4})[-/](?P<m>\d{1,2})$"),
    re.compile(r"^(?P<y>1[89]\d{2}|20\d{2})$"),
]


def format_date(date_str: str) -> str:
    """Formata uma string de data em português para exibição na capa."""
    if not date_str:
        return ""
    raw = str(date_str).strip()

    m = _HISTORICAL_ERA.match(raw)
    if m:
        prefix = m.group("prefix") or ""
        year   = m.group("year")
        era_raw = m.group("era") or ""

        era = ""
        if era_raw:
            era_clean = re.sub(r"\s+", "", era_raw.lower())
            if "ac" in era_clean or "a.c" in era_clean:
                era = "a.C."
            elif "dc" in era_clean or "d.c" in era_clean:
                era = "d.C."

        if era or prefix:
            parts = []
            if prefix:
                parts.append("c.")
            parts.append(year)
            if era:
                parts.append(era)
            return " ".join(parts)

    for pattern in _MODERN_DATE_PATTERNS:
        m2 = pattern.match(raw)
        if m2:
            groups = m2.groupdict()
            year  = groups.get("y", "")
            month = int(groups.get("m", 0))
            day   = int(groups.get("d", 0))

            if day and month and year:
                if 1 <= month <= 12:
                    return f"{day} de {_MONTHS_BR[month - 1]} de {year}"
            elif month and year:
                if 1 <= month <= 12:
                    return f"{_MONTHS_BR[month - 1]} de {year}"
            elif year:
                return year

    return raw


# ══════════════════════════════════════════════════════════════════════════════
# Extração de Metadados
# ══════════════════════════════════════════════════════════════════════════════

def extract_authors(metadata: dict) -> str:
    for key in ("authors", "author"):
        value = metadata.get(key)
        if value:
            if isinstance(value, list):
                return ", ".join(
                    a.get("name", str(a)) if isinstance(a, dict) else str(a)
                    for a in value
                )
            return str(value)
    return ""


def find_markdown_metadata(
    base_dir: str, target_input: str
) -> tuple[dict, bool, str]:
    """
    Localiza e retorna (metadata, is_book, slug) para um dado slug ou caminho.
    Busca em content/ e data/review/.
    """
    base_path = Path(base_dir)
    target_path = Path(target_input)

    candidates = [
        target_path,
        base_path / target_path,
        target_path.with_suffix(".md"),
        (base_path / target_path).with_suffix(".md"),
    ]
    for c in candidates:
        if c.is_file():
            c_resolved = c.resolve()
            c_str = str(c_resolved)
            is_b = "/books/" in c_str or "books" in c_resolved.parts
            return parse_markdown_file(c_str).get("metadata", {}), is_b, c.stem

    stem = target_path.stem
    variants = [
        f"{stem}.md",
        stem.replace("_", "-") + ".md",
        stem.replace("-", "_") + ".md",
    ]
    search_dirs = [
        (base_path / "content" / "books", True),
        (base_path / "data" / "review" / "books", True),
        (base_path / "content" / "articles", False),
        (base_path / "data" / "review" / "articles", False),
    ]
    for variant in variants:
        for s_dir, is_b in search_dirs:
            if s_dir.exists():
                for p in s_dir.rglob(variant):
                    if p.is_file():
                        return parse_markdown_file(str(p)).get("metadata", {}), is_b, p.stem

    return {}, False, stem


# ══════════════════════════════════════════════════════════════════════════════
# Composição Tipográfica (Ilustração Full Bleed)
# ══════════════════════════════════════════════════════════════════════════════

def inject_cover_text(
    base_dir: str,
    raw_image_path: str,
    custom_text: str = None,
    target_slug: str = None,
) -> None:
    """
    Compõe a capa final com a ilustração temática ocupando 100% da área (full bleed)
    e tipografia nobre centralizada sobreposta.
    """
    img_path = Path(raw_image_path).resolve()
    if not img_path.exists():
        print(f"❌ Imagem não encontrada: {img_path}")
        return

    base_name = target_slug or re.sub(r"^\.?tmp_raw_", "", img_path.stem)

    title = subtitle = authors = date_raw = ""
    is_book = False

    if custom_text:
        parts = [p.strip() for p in custom_text.split("|")]
        title   = parts[0] if len(parts) > 0 else ""
        authors = parts[1] if len(parts) > 1 else ""
        date_raw = parts[2] if len(parts) > 2 else ""
        is_book = not bool(date_raw)
    else:
        metadata, is_book, canonical_slug = find_markdown_metadata(base_dir, base_name)
        if metadata:
            base_name = canonical_slug
            title     = metadata.get("title", base_name)
            authors   = extract_authors(metadata)
            date_raw  = str(metadata.get("date", ""))
        else:
            print("⚠️  Markdown não encontrado — usando nome do arquivo como título.")
            title = base_name.replace("-", " ").replace("_", " ").title()

    if not subtitle and ":" in title:
        title, subtitle = (p.strip() for p in title.split(":", 1))

    date_display = format_date(date_raw)

    print(
        f"🎨 Compondo capa (ilustração ocupando toda a capa):\n"
        f"   Tipo     : {'Livro' if is_book else 'Artigo'}\n"
        f"   Título   : {title}\n"
        f"   Subtítulo: {subtitle or '(nenhum)'}\n"
        f"   Autor(es): {authors}\n"
        f"   Data     : {date_display or '(nenhuma)'}"
    )

    W, H = CANVAS_W, CANVAS_H

    # 1. Carrega e redimensiona a imagem para ocupar 100% da capa (full bleed)
    try:
        with Image.open(img_path) as raw_img:
            raw_img = raw_img.convert("RGBA")
            scale = max(W / raw_img.width, H / raw_img.height)
            new_w = round(raw_img.width * scale)
            new_h = round(raw_img.height * scale)
            raw_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            x_off = (new_w - W) // 2
            y_off = (new_h - H) // 2
            bg_img = raw_img.crop((x_off, y_off, x_off + W, y_off + H))
    except Exception as exc:
        print(f"❌ Erro ao carregar a imagem de fundo: {exc}")
        return

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    draw_sh = ImageDraw.Draw(shadow)

    # 2. Configura tipografia adaptativa (título monumental legível em telas mobile)
    max_text_w = 1480

    # Título principal monumental
    title_len = len(title)
    if title_len < 25:
        title_fs = 195
    elif title_len < 48:
        title_fs = 165
    elif title_len < 70:
        title_fs = 140
    else:
        title_fs = 120

    title_font = _load_font("bold", title_fs)
    title_lines = _wrap_to_width(draw, title, title_font, max_text_w)
    title_line_h = int(title_fs * 1.24)

    # Subtítulo (se houver)
    sub_font = None
    sub_lines = []
    sub_line_h = 0
    if subtitle:
        sub_fs = 115 if len(subtitle) < 30 else 90
        sub_font = _load_font("regular", sub_fs)
        sub_lines = _wrap_to_width(draw, subtitle, sub_font, max_text_w)
        sub_line_h = int(sub_fs * 1.25)

    # Autor: subordinado e visivelmente menor que o título (50% a 60% da altura do título)
    author_font = None
    author_text = ""
    if authors:
        author_fs = max(int(title_fs * 0.55), 65)
        author_font = _load_font("semibold", author_fs)
        author_text = authors.title() if authors.isupper() else authors

    # Posição vertical inicial no terço superior
    curr_y = 260

    # Renderiza Título (Matte Gold #E2C974 com sombra suave)
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw_sh.text((x + 4, curr_y + 5), line, font=title_font, fill=COLOR_SHADOW)
        draw.text((x, curr_y), line, font=title_font, fill=COLOR_TITLE)
        curr_y += title_line_h

    curr_y += 35

    # Renderiza Subtítulo (Crisp White #FFFFFF com sombra suave)
    if subtitle and sub_font:
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            line_w = bbox[2] - bbox[0]
            x = (W - line_w) // 2
            draw_sh.text((x + 3, curr_y + 4), line, font=sub_font, fill=COLOR_SHADOW)
            draw.text((x, curr_y), line, font=sub_font, fill=COLOR_SUBTITLE)
            curr_y += sub_line_h
        curr_y += 30

    # Renderiza Autor (Soft White #F8FAFC com sombra suave)
    if authors and author_font:
        curr_y += 20
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw_sh.text((x + 3, curr_y + 4), author_text, font=author_font, fill=COLOR_SHADOW)
        draw.text((x, curr_y), author_text, font=author_font, fill=COLOR_AUTHOR)

    # Renderiza Data (se artigo, ou quando presente, na base da capa)
    if date_display and not is_book:
        date_font = _load_font("regular", 68)
        date_y = H - 190
        bbox = draw.textbbox((0, 0), date_display, font=date_font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw_sh.text((x + 3, date_y + 3), date_display, font=date_font, fill=COLOR_SHADOW)
        draw.text((x, date_y), date_display, font=date_font, fill=COLOR_DATE)

    # Suaviza a sombra com filtro Gaussiano para profundidade natural
    shadow_blurred = shadow.filter(ImageFilter.GaussianBlur(radius=5))

    # Composição final sobre a ilustração full-bleed
    final_img = Image.alpha_composite(bg_img, shadow_blurred)
    final_img = Image.alpha_composite(final_img, overlay).convert("RGB")

    # Salva na pasta originals/
    originals_dir = Path(base_dir) / "assets" / "covers" / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)
    dest_path = originals_dir / f"{base_name}.png"
    final_img.save(dest_path, format="PNG", quality=95)
    print(f"✅ Capa gerada: {dest_path}")

    # Remove imagem temporária se aplicável
    if (
        img_path != dest_path
        and img_path.exists()
        and img_path.parent == Path(base_dir) / "assets" / "covers"
    ):
        img_path.unlink()
        print(f"🧹 Temporário removido: {img_path.name}")


# ══════════════════════════════════════════════════════════════════════════════
# Conversão e Redimensionamento Responsivo
# ══════════════════════════════════════════════════════════════════════════════

def _should_convert(original_path: Path, covers_dir: Path, force: bool = False) -> bool:
    if force:
        return True
    output_name = f"{original_path.stem}.webp"
    orig_mtime = original_path.stat().st_mtime
    for size_name in SCREEN_SIZES:
        dest = covers_dir / size_name / output_name
        if not dest.exists() or dest.stat().st_mtime < orig_mtime:
            return True
    return False


def convert_covers(base_dir: str, target_file: str = None, force: bool = False) -> None:
    covers_dir    = Path(base_dir) / "assets" / "covers"
    originals_dir = covers_dir / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)

    for size_name in SCREEN_SIZES:
        (covers_dir / size_name).mkdir(parents=True, exist_ok=True)

    print(f"🖼️  Iniciando conversão de capas em: {covers_dir}\n")

    files: list[Path] = []
    if target_file:
        target_path = Path(target_file)
        name = target_path.name
        if (originals_dir / name).exists():
            files = [originals_dir / name]
        elif target_path.exists() and target_path.is_file():
            files = [target_path]
        else:
            stem = target_path.stem
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                candidate = originals_dir / f"{stem}{ext}"
                if candidate.exists():
                    files = [candidate]
                    break
            if not files:
                print(f"❌ Arquivo não encontrado: {target_file}")
                return
    else:
        valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
        files = [f for f in originals_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]

    processed = 0
    skipped   = 0

    for f in sorted(files):
        output_name = f"{f.stem}.webp"

        if not _should_convert(f, covers_dir, force=force):
            skipped += 1
            continue

        print(f"⏳ Processando: {f.name}")
        try:
            with Image.open(f) as img:
                img_rgb = img.convert("RGB")
                orig_w, orig_h = img_rgb.size
                aspect = orig_h / orig_w

                for size_name, target_w in SCREEN_SIZES.items():
                    target_h   = round(target_w * aspect)
                    dest_file  = covers_dir / size_name / output_name
                    resized    = img_rgb.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    resized.info["dpi"] = TARGET_DPI
                    resized.save(dest_file, format="WEBP", quality=85)
                    print(f"   ✅ {size_name} ({target_w}×{target_h}px) → covers/{size_name}/{output_name}")

            processed += 1
        except Exception as exc:
            print(f"   ❌ Erro ao processar {f.name}: {exc}")

    print(f"\n🎉 Concluído: {processed} processadas, {skipped} ignoradas.")
