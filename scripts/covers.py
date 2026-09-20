"""
covers.py — Sistema de composição editorial de capas do OpenSciMD.

Layout em 3 zonas fixas (proporcional à resolução):
  ┌──────────────────────────────────────┐
  │  ZONA DE TEXTO (~40%)                │  ← fundo sólido escuro
  │  [badge tipo]  título  autor         │
  ├──────────────────────────────────────┤  ← fio espesso (livros) ou nenhum (artigos)
  │                                      │
  │  ZONA DA IMAGEM (~48%)               │  ← ilustração/pintura temática
  │                                      │
  ├──────────────────────────────────────┤  ← fio espesso (ambos)
  │  ZONA DO RODAPÉ (~12%)               │  ← data histórica ou de publicação
  └──────────────────────────────────────┘

Diferenciação visual livro × artigo:
  - Livro : badge "LIVRO" (borda dourada), fio dourado superior e inferior da imagem
  - Artigo: badge "ARTIGO" (borda vermelha), sem fio superior, fio vermelho inferior da imagem

Paleta de cores:
  - Fundo         : #0F1117
  - Título (ouro) : #D4A847
  - Subtítulo     : #F5EED8
  - Autor         : #FFFFFF
  - Data (rodapé) : #CBD5E1
  - Fio livro     : #D4A847
  - Fio artigo    : #8B1A1A
  - Badge livro   : #D4A847 (texto e borda)
  - Badge artigo  : #C0392B (texto e borda)

Fonte: Cormorant Garamond (Bold, SemiBold, Regular, SC)
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

# ── Proporções das zonas (soma = 1.0) ─────────────────────────────────────────
TEXT_ZONE_RATIO  = 0.40
IMAGE_ZONE_RATIO = 0.48
FOOTER_ZONE_RATIO = 0.12

# ── Margens internas da zona de texto ─────────────────────────────────────────
TEXT_MARGIN_X = 96   # margem horizontal esquerda/direita
TEXT_MARGIN_TOP = 72  # distância do topo até o primeiro elemento de texto

# ── Paleta ─────────────────────────────────────────────────────────────────────
COLOR_BG           = (15, 17, 23)         # #0F1117
COLOR_TITLE        = (212, 168, 71, 255)  # #D4A847
COLOR_SUBTITLE     = (245, 238, 216, 255) # #F5EED8
COLOR_AUTHOR       = (255, 255, 255, 255) # #FFFFFF
COLOR_DATE         = (203, 213, 225, 240) # #CBD5E1
COLOR_RULE_BOOK    = (212, 168, 71, 255)  # #D4A847
COLOR_RULE_ARTICLE = (139, 26, 26, 255)   # #8B1A1A
COLOR_BADGE_BOOK   = (212, 168, 71, 255)
COLOR_BADGE_ARTICLE = (192, 57, 43, 255)  # #C0392B
COLOR_SHADOW       = (0, 0, 0, 200)

# ── Espessuras de linha ────────────────────────────────────────────────────────
RULE_TOP_PX    = 1   # fio fino horizontal no topo (acima do badge)
RULE_THICK_PX  = 3   # fio espesso nos limites da zona da imagem

# ── Tamanhos de fonte: máximo e mínimo (em px, na resolução canônica) ─────────
TITLE_FONT_MAX  = 195
TITLE_FONT_MIN  = 72
SUBTITLE_FONT_MAX = 110
SUBTITLE_FONT_MIN = 56
AUTHOR_FONT_MAX  = 100
AUTHOR_FONT_MIN  = 56
DATE_FONT_SIZE   = 70
BADGE_FONT_SIZE  = 42

# ── Caminhos de fonte (Cormorant Garamond, instalado via ttf-cormorant) ────────
FONT_DIR = Path("/usr/share/fonts/TTF")

FONTS = {
    "bold"     : FONT_DIR / "CormorantGaramond-Bold.ttf",
    "semibold"  : FONT_DIR / "CormorantGaramond-SemiBold.ttf",
    "regular"  : FONT_DIR / "CormorantGaramond-Regular.ttf",
    "small_caps": FONT_DIR / "CormorantSC-SemiBold.ttf",
}

# Fallback em ordem de preferência (caso Cormorant não esteja instalado)
FONT_FALLBACKS = {
    "bold"     : ["/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf"],
    "semibold"  : ["/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf"],
    "regular"  : ["/usr/share/fonts/gsfonts/NimbusRoman-Regular.otf",
                  "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf"],
    "small_caps": ["/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf",
                   "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf"],
}

# ── Tamanhos de saída por tela ─────────────────────────────────────────────────
SCREEN_SIZES = {
    "mobile" : 1080,
    "tablet" : 1200,
    "desktop": 1696,
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
    # último recurso: qualquer fonte bold/regular do sistema
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
    line_spacing_factor: float = 1.28,
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
    # fallback: usa o mínimo mesmo que ultrapasse
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

# Padrões para datas históricas (pré-modernas)
# Captura: opcional prefixo (c., ca., aprox.), número, era (a.C. / d.C.)
_HISTORICAL_ERA = re.compile(
    r"^"
    r"(?P<prefix>c\.|ca\.|aprox\.)?\s*"
    r"(?P<year>\d{1,4})"
    r"\s*"
    r"(?P<era>a\.?\s*C\.?|d\.?\s*C\.?)?"
    r"$",
    re.IGNORECASE,
)

# Padrões para datas de publicação modernas
_MODERN_DATE_PATTERNS = [
    # dd-mm-yyyy ou dd/mm/yyyy
    re.compile(r"^(?P<d>\d{1,2})[-/](?P<m>\d{1,2})[-/](?P<y>\d{4})$"),
    # yyyy-mm-dd ou yyyy/mm/dd
    re.compile(r"^(?P<y>\d{4})[-/](?P<m>\d{1,2})[-/](?P<d>\d{1,2})$"),
    # mm-yyyy ou mm/yyyy
    re.compile(r"^(?P<m>\d{1,2})[-/](?P<y>\d{4})$"),
    # yyyy-mm
    re.compile(r"^(?P<y>\d{4})[-/](?P<m>\d{1,2})$"),
    # Apenas o ano moderno (1800–2099)
    re.compile(r"^(?P<y>1[89]\d{2}|20\d{2})$"),
]


def format_date(date_str: str) -> str:
    """
    Formata uma string de data em português para exibição no rodapé da capa.

    Suporta:
      - Datas modernas: dd-mm-yyyy, yyyy-mm-dd, yyyy-mm, mm-yyyy, yyyy
      - Datas históricas: "399 a.C.", "c. 1130 d.C.", "386 d.C", "107 d. C.", "1418 d.C."
      - Anos soltos que parecem históricos mas são modernos (ex.: "1997", "1576", "1912")
    """
    if not date_str:
        return ""
    raw = str(date_str).strip()

    # 1. Tentar padrão histórico (com era a.C./d.C. ou prefixo "c.")
    m = _HISTORICAL_ERA.match(raw)
    if m:
        prefix = m.group("prefix") or ""
        year   = m.group("year")
        era_raw = m.group("era") or ""

        # Normaliza era
        era = ""
        if era_raw:
            era_clean = re.sub(r"\s+", "", era_raw.lower())
            if "ac" in era_clean or "a.c" in era_clean:
                era = "a.C."
            elif "dc" in era_clean or "d.c" in era_clean:
                era = "d.C."

        # Só é histórico se vier com era explícita ou prefixo aproximação
        if era or prefix:
            parts = []
            if prefix:
                parts.append("c.")  # normaliza para "c."
            parts.append(year)
            if era:
                parts.append(era)
            return " ".join(parts)

    # 2. Tentar padrões de data moderna
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

    # 3. Devolve como está (ex.: "Século III", strings não reconhecidas)
    return raw


# ══════════════════════════════════════════════════════════════════════════════
# Extração de metadados do Markdown
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

    Busca em ordem:
      1. Caminho direto (relativo ao cwd ou base_dir)
      2. Busca recursiva em content/books → is_book=True
      3. Busca recursiva em content/articles → is_book=False
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
            books_dir    = (base_path / "content" / "books").resolve()
            articles_dir = (base_path / "content" / "articles").resolve()
            if str(c_resolved).startswith(str(books_dir)):
                return parse_markdown_file(str(c_resolved)).get("metadata", {}), True, c.stem
            elif str(c_resolved).startswith(str(articles_dir)):
                return parse_markdown_file(str(c_resolved)).get("metadata", {}), False, c.stem

    stem = target_path.stem
    variants = [
        f"{stem}.md",
        stem.replace("_", "-") + ".md",
        stem.replace("-", "_") + ".md",
    ]
    for variant in variants:
        for p in (base_path / "content" / "books").rglob(variant):
            if p.is_file():
                return parse_markdown_file(str(p)).get("metadata", {}), True, p.stem
        for p in (base_path / "content" / "articles").rglob(variant):
            if p.is_file():
                return parse_markdown_file(str(p)).get("metadata", {}), False, p.stem

    return {}, False, stem


# ══════════════════════════════════════════════════════════════════════════════
# Conversão / redimensionamento de capas
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
    covers_dir   = Path(base_dir) / "assets" / "covers"
    originals_dir = covers_dir / "originals"

    print(f"🖼️  Iniciando conversão de capas em: {covers_dir}")

    if not covers_dir.exists():
        print(f"❌ Erro: Diretório {covers_dir} não encontrado.")
        return

    originals_dir.mkdir(parents=True, exist_ok=True)
    for size in SCREEN_SIZES:
        (covers_dir / size).mkdir(parents=True, exist_ok=True)

    # Migra arquivos soltos na raiz de covers/ para originals/
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    for item in covers_dir.iterdir():
        if item.is_file() and item.suffix.lower() in image_exts:
            item.rename(originals_dir / item.name)
            print(f"📦 Migrado para originals/: {item.name}")

    # Seleciona arquivos a processar
    if target_file:
        target_path = Path(target_file)
        name = target_path.name
        if (originals_dir / name).exists():
            files = [originals_dir / name]
        elif target_path.exists() and target_path.is_file():
            files = [target_path]
        else:
            print(f"❌ Arquivo alvo não encontrado em originals/: {name}")
            return
    else:
        files = [f for f in originals_dir.iterdir()
                 if f.is_file() and f.suffix.lower() in image_exts]

    processed = skipped = 0
    for file in files:
        output_name = f"{file.stem}.webp"
        if not _should_convert(file, covers_dir, force=force):
            print(f"⏭️  Ignorando (sem alterações): {file.name}")
            skipped += 1
            continue

        print(f"\n⏳ Processando: {file.name}")
        try:
            with Image.open(file) as img:
                for size_name, target_w in SCREEN_SIZES.items():
                    target_h = round(target_w * (CANVAS_H / CANVAS_W))
                    out_path = covers_dir / size_name / output_name
                    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    resized.save(out_path, format="WEBP", quality=85)
                    print(f"   ✅ {size_name} ({target_w}×{target_h}px) → covers/{size_name}/{output_name}")
            processed += 1
        except Exception as exc:
            print(f"   ❌ Erro ao converter {file.name}: {exc}")

    print(f"\n🎉 Concluído: {processed} processadas, {skipped} ignoradas.")


# ══════════════════════════════════════════════════════════════════════════════
# Composição tipográfica da capa (inject_cover_text)
# ══════════════════════════════════════════════════════════════════════════════

def _draw_text_centered(
    draw: ImageDraw.ImageDraw,
    draw_shadow: ImageDraw.ImageDraw,
    text: str,
    font,
    y: int,
    canvas_w: int,
    color: tuple,
    shadow_offset: int = 3,
) -> None:
    """Desenha uma linha de texto centralizada com sombra suave."""
    w = _text_width(draw, text, font)
    x = (canvas_w - w) // 2
    draw_shadow.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=COLOR_SHADOW)
    draw.text((x, y), text, font=font, fill=color)


def _draw_badge(
    draw: ImageDraw.ImageDraw,
    label: str,
    canvas_w: int,
    color: tuple,
    margin_right: int = 56,
    margin_top: int = 44,
    padding_x: int = 18,
    padding_y: int = 10,
) -> None:
    """Desenha o badge de tipo (LIVRO / ARTIGO) no canto superior direito."""
    font = _load_font("small_caps", BADGE_FONT_SIZE)
    text_w = _text_width(draw, label, font)
    text_h = _text_height(draw, label, font)

    box_w = text_w + padding_x * 2
    box_h = text_h + padding_y * 2

    x1 = canvas_w - margin_right - box_w
    y1 = margin_top
    x2 = canvas_w - margin_right
    y2 = margin_top + box_h

    # Fundo semitransparente + borda 1px
    border_color = (*color[:3], 200)
    fill_color   = (*color[:3], 28)
    draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=border_color, width=1)

    tx = x1 + padding_x
    ty = y1 + padding_y
    draw.text((tx, ty), label, font=font, fill=(*color[:3], 220))


def _draw_rule(
    draw: ImageDraw.ImageDraw,
    y: int,
    canvas_w: int,
    color: tuple,
    thickness: int,
    margin_x: int = 0,
) -> None:
    """Desenha uma linha horizontal de divisão."""
    draw.rectangle(
        [margin_x, y, canvas_w - margin_x, y + thickness],
        fill=color,
    )


def inject_cover_text(
    base_dir: str,
    raw_image_path: str,
    custom_text: str = None,
    target_slug: str = None,
) -> None:
    """
    Compõe a capa final com layout em 3 zonas fixas sobre uma imagem temática.

    Parâmetros
    ----------
    base_dir        : raiz do projeto
    raw_image_path  : caminho para a imagem bruta (a ser usada na zona central)
    custom_text     : string "título|autor|data" para substituir metadados Markdown
    target_slug     : slug canônico do documento (sobrescreve a detecção automática)
    """
    img_path = Path(raw_image_path).resolve()
    if not img_path.exists():
        print(f"❌ Imagem não encontrada: {img_path}")
        return

    base_name = target_slug or re.sub(r"^\.?tmp_raw_", "", img_path.stem)

    # ── Coleta de metadados ────────────────────────────────────────────────────
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

    # Separa título e subtítulo se houver ":"
    if not subtitle and ":" in title:
        title, subtitle = (p.strip() for p in title.split(":", 1))

    date_display = format_date(date_raw)

    print(
        f"🎨 Compondo capa:\n"
        f"   Tipo     : {'Livro' if is_book else 'Artigo'}\n"
        f"   Título   : {title}\n"
        f"   Subtítulo: {subtitle or '(nenhum)'}\n"
        f"   Autor(es): {authors}\n"
        f"   Data     : {date_display or '(nenhuma)'}"
    )

    # ── Preparação do canvas ───────────────────────────────────────────────────
    W, H = CANVAS_W, CANVAS_H

    text_zone_h   = round(H * TEXT_ZONE_RATIO)
    image_zone_h  = round(H * IMAGE_ZONE_RATIO)
    footer_zone_h = H - text_zone_h - image_zone_h

    image_zone_top    = text_zone_h
    image_zone_bottom = text_zone_h + image_zone_h
    footer_zone_top   = image_zone_bottom

    # Canvas base (fundo sólido escuro)
    canvas = Image.new("RGB", (W, H), COLOR_BG)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    draw_sh = ImageDraw.Draw(shadow)

    # ── Zona da imagem ─────────────────────────────────────────────────────────
    try:
        with Image.open(img_path) as raw_img:
            raw_img = raw_img.convert("RGBA")

            # Recorta/redimensiona a imagem para preencher a zona central
            scale = max(W / raw_img.width, image_zone_h / raw_img.height)
            new_w = round(raw_img.width * scale)
            new_h = round(raw_img.height * scale)
            raw_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Centraliza e corta
            x_off = (new_w - W) // 2
            y_off = (new_h - image_zone_h) // 2
            cropped = raw_img.crop((x_off, y_off, x_off + W, y_off + image_zone_h))

            # Vinheta: funde a imagem com as zonas sólidas escuras adjacentes
            # Topo: fade suave para não criar uma borda dura abaixo do fio
            # Base: fade suave para fundir com o rodapé sólido
            vignette = Image.new("RGBA", (W, image_zone_h), (0, 0, 0, 0))
            vdraw    = ImageDraw.Draw(vignette)

            top_fade_h    = round(image_zone_h * 0.18)   # 18% do topo
            bottom_fade_h = round(image_zone_h * 0.14)   # 14% da base

            for i in range(top_fade_h):
                # Começa em alpha 160, termina em 0 conforme desce
                alpha = int(160 * (1 - i / top_fade_h) ** 1.5)
                vdraw.rectangle([0, i, W, i + 1], fill=(0, 0, 0, alpha))

            for i in range(bottom_fade_h):
                # Começa em 0, cresce até 140 conforme sobe
                alpha = int(140 * (i / bottom_fade_h) ** 1.4)
                vdraw.rectangle(
                    [0, image_zone_h - bottom_fade_h + i, W, image_zone_h - bottom_fade_h + i + 1],
                    fill=(0, 0, 0, alpha),
                )

            zone_img = Image.alpha_composite(cropped, vignette).convert("RGB")
            canvas.paste(zone_img, (0, image_zone_top))

    except Exception as exc:
        print(f"⚠️  Não foi possível carregar a imagem temática: {exc}")
        # Capa continua com fundo sólido escuro se a imagem falhar

    # ── Linhas de fio (reglets) ────────────────────────────────────────────────
    rule_color = COLOR_RULE_BOOK if is_book else COLOR_RULE_ARTICLE

    # Fio fino no topo absoluto (acima do badge, sempre presente)
    _draw_rule(draw, y=0, canvas_w=W, color=rule_color, thickness=RULE_TOP_PX)

    # Fio espesso no topo da zona de imagem — apenas em livros
    if is_book:
        _draw_rule(
            draw,
            y=image_zone_top - RULE_THICK_PX,
            canvas_w=W,
            color=rule_color,
            thickness=RULE_THICK_PX,
        )

    # Fio espesso no rodapé (ambos os tipos)
    _draw_rule(
        draw,
        y=footer_zone_top,
        canvas_w=W,
        color=rule_color,
        thickness=RULE_THICK_PX,
    )

    # ── Badge de tipo ──────────────────────────────────────────────────────────
    badge_label = "LIVRO" if is_book else "ARTIGO"
    badge_color = COLOR_BADGE_BOOK if is_book else COLOR_BADGE_ARTICLE
    _draw_badge(draw, badge_label, W, badge_color)

    # ── Zona de texto — renderização em dois passos ────────────────────────────
    #
    # Passo 1: calcula fonte e linhas de cada elemento SEM desenhar.
    # Passo 2: mede a altura total do bloco e centraliza verticalmente na zona.
    #
    max_text_w = W - TEXT_MARGIN_X * 2

    # Espaço disponível para escalonamento de cada elemento
    # (não varia entre capas — é baseado na zona fixa)
    text_zone_inner_h = text_zone_h - TEXT_MARGIN_TOP * 2
    title_avail    = round(text_zone_inner_h * 0.55)
    subtitle_avail = round(text_zone_inner_h * 0.25)
    author_avail   = round(text_zone_inner_h * 0.20)

    # Gaps fixos entre elementos (em px)
    GAP_TITLE_SUBTITLE = 18
    GAP_SUBTITLE_AUTHOR = 20
    GAP_TITLE_AUTHOR = 28   # quando não há subtítulo

    # ── Passo 1: determina fontes e linhas ─────────────────────────────────────
    title_text = title.upper()
    title_font, title_lines, title_fs = _fit_font_to_zone(
        draw, title_text, "bold",
        max_text_w, title_avail,
        TITLE_FONT_MAX, TITLE_FONT_MIN,
        line_spacing_factor=1.22,
    )
    title_line_h = int(title_fs * 1.22)
    title_block_h = title_line_h * len(title_lines)

    sub_font = sub_lines = sub_fs = None
    subtitle_block_h = 0
    if subtitle:
        sub_font, sub_lines, sub_fs = _fit_font_to_zone(
            draw, subtitle, "regular",
            max_text_w, subtitle_avail,
            SUBTITLE_FONT_MAX, SUBTITLE_FONT_MIN,
            line_spacing_factor=1.28,
        )
        sub_line_h = int(sub_fs * 1.28)
        subtitle_block_h = sub_line_h * len(sub_lines)

    author_font = author_lines = author_fs = None
    author_block_h = 0
    if authors:
        author_text = authors.title() if authors.isupper() else authors
        author_font, author_lines, author_fs = _fit_font_to_zone(
            draw, author_text, "semibold",
            max_text_w, author_avail,
            AUTHOR_FONT_MAX, AUTHOR_FONT_MIN,
            line_spacing_factor=1.3,
        )
        author_line_h = int(author_fs * 1.3)
        author_block_h = author_line_h * len(author_lines)

    # ── Passo 2: calcula altura total do bloco e centraliza na zona ────────────
    total_block_h = title_block_h
    if subtitle_block_h:
        total_block_h += GAP_TITLE_SUBTITLE + subtitle_block_h
    if author_block_h:
        gap = GAP_SUBTITLE_AUTHOR if subtitle_block_h else GAP_TITLE_AUTHOR
        total_block_h += gap + author_block_h

    # Offset vertical para centrar o bloco na zona de texto
    curr_y = (text_zone_h - total_block_h) // 2
    # Garante margem mínima no topo (badge tem ~100px de altura)
    curr_y = max(curr_y, TEXT_MARGIN_TOP + 30)

    # ── Renderiza Título ───────────────────────────────────────────────────────
    for line in title_lines:
        _draw_text_centered(draw, draw_sh, line, title_font, curr_y, W, COLOR_TITLE)
        curr_y += title_line_h

    # ── Renderiza Subtítulo ────────────────────────────────────────────────────
    if subtitle and sub_font:
        curr_y += GAP_TITLE_SUBTITLE
        for line in sub_lines:
            _draw_text_centered(draw, draw_sh, line, sub_font, curr_y, W, COLOR_SUBTITLE)
            curr_y += sub_line_h

    # ── Renderiza Autor ────────────────────────────────────────────────────────
    if authors and author_font:
        curr_y += GAP_SUBTITLE_AUTHOR if subtitle else GAP_TITLE_AUTHOR
        for line in author_lines:
            _draw_text_centered(draw, draw_sh, line, author_font, curr_y, W, COLOR_AUTHOR)
            curr_y += author_line_h

    # ── Zona do rodapé (apenas data) ───────────────────────────────────────────

    if date_display:
        date_font = _load_font("regular", DATE_FONT_SIZE)
        date_y = footer_zone_top + (footer_zone_h - DATE_FONT_SIZE) // 2
        _draw_text_centered(draw, draw_sh, date_display, date_font, date_y, W, COLOR_DATE)

    # ── Composição final ───────────────────────────────────────────────────────
    shadow_blurred = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba = Image.alpha_composite(canvas_rgba, shadow_blurred)
    canvas_rgba = Image.alpha_composite(canvas_rgba, overlay)
    final = canvas_rgba.convert("RGB")

    # ── Salva na pasta originals/ ──────────────────────────────────────────────
    originals_dir = Path(base_dir) / "assets" / "covers" / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)
    dest_path = originals_dir / f"{base_name}.png"
    final.save(dest_path, format="PNG")
    print(f"✅ Capa gerada: {dest_path}")

    # Remove imagem temporária se aplicável
    if (
        img_path != dest_path
        and img_path.exists()
        and img_path.parent == Path(base_dir) / "assets" / "covers"
    ):
        img_path.unlink()
        print(f"🧹 Temporário removido: {img_path.name}")
