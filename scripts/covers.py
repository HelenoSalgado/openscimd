import os
import subprocess
from pathlib import Path
from PIL import Image
from scripts.utils import parse_markdown_file

TARGET_WIDTH = 1696
TARGET_HEIGHT = 2528
TARGET_DPI = (72, 72)

SCREEN_SIZES = {
    'mobile': 1080,
    'tablet': 1200,
    'desktop': 1696
}

def should_convert(original_path: Path, covers_dir: Path, force: bool = False) -> bool:
    if force:
        return True
        
    output_name = f"{original_path.stem}.webp"
    orig_mtime = original_path.stat().st_mtime
    
    for size_name in SCREEN_SIZES.keys():
        dest_path = covers_dir / size_name / output_name
        if not dest_path.exists():
            return True
        if dest_path.stat().st_mtime < orig_mtime:
            return True
            
    return False

def convert_covers(base_dir: str, target_file: str = None, force: bool = False):
    covers_dir = Path(base_dir) / 'assets' / 'covers'
    print(f'🖼️  Iniciando a conversão de capas em: {covers_dir}')
    
    if not covers_dir.exists():
        print(f"Erro: Diretório {covers_dir} não encontrado.")
        return
        
    originals_dir = covers_dir / 'originals'
    originals_dir.mkdir(parents=True, exist_ok=True)
    
    for size in SCREEN_SIZES.keys():
        (covers_dir / size).mkdir(parents=True, exist_ok=True)
        
    image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    
    for item in covers_dir.iterdir():
        if item.is_file() and item.suffix.lower() in image_exts:
            item.rename(originals_dir / item.name)
            print(f"📦 Mapeado original para pasta originals: {item.name}")
            
    files = []
    if target_file:
        target_path = Path(target_file)
        name = target_path.name
        if (originals_dir / name).exists():
            files = [originals_dir / name]
        elif target_path.exists() and target_path.is_file():
            files = [target_path]
        else:
            print(f"❌ Erro: O arquivo alvo {name} não foi encontrado em {originals_dir}")
            return
    else:
        files = [f for f in originals_dir.iterdir() if f.is_file() and f.suffix.lower() in image_exts]
        
    processed = 0
    skipped = 0
    for file in files:
        output_name = f"{file.stem}.webp"
        
        if not should_convert(file, covers_dir, force=force):
            print(f"⏭️  Ignorando (já atualizado): {file.name}")
            skipped += 1
            continue
            
        print(f"\n⏳ Processando capa: {file.name}")
        
        try:
            with Image.open(file) as img:
                for size_name, target_w in SCREEN_SIZES.items():
                    target_h = round(target_w * (TARGET_HEIGHT / TARGET_WIDTH))
                    output_path = covers_dir / size_name / output_name
                    print(f"   -> Convertendo para {size_name} ({target_w}x{target_h}px)...")
                    
                    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    resized.info['dpi'] = TARGET_DPI
                    resized.save(output_path, format="WEBP", quality=85)
                    print(f"   ✅ Salvo em: covers/{size_name}/{output_name}")
            processed += 1
        except Exception as e:
            print(f"   ❌ Erro ao converter {file.name}: {e}")
            
    print(f"\n🎉 Processamento concluído! {processed} capas processadas, {skipped} ignoradas (sem alterações).")

def format_date(date_str):
    if not date_str: return ''
    import re
    s = str(date_str).strip()
    monthsBR = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    m = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', s)
    if m:
        p1, p2, year = int(m.group(1)), int(m.group(2)), m.group(3)
        month, day = p2, p1 if p1 <= 12 else p2
        if p1 > 12: day, month = p1, p2
        elif p2 > 12: month, day = p1, p2
        
        if 1 <= month <= 12:
            return f"{day} de {monthsBR[month-1]} de {year}"
            
    m2 = re.match(r'^(\d{4})[-/](\d{1,2})$', s) or re.match(r'^(\d{1,2})[-/](\d{4})$', s)
    if m2:
        m_val, y_val = int(m2.group(1)), m2.group(2)
        if m_val > 12:
            y_val, m_val = m2.group(1), int(m2.group(2))
        if 1 <= m_val <= 12:
            return f"{monthsBR[m_val-1]} de {y_val}"
            
    return s

def extract_authors(metadata):
    authors = metadata.get('authors')
    if authors:
        if isinstance(authors, list):
            return ", ".join([a.get('name', str(a)) if isinstance(a, dict) else str(a) for a in authors])
        return str(authors)
    author = metadata.get('author')
    if author:
        if isinstance(author, list):
            return ", ".join([a.get('name', str(a)) if isinstance(a, dict) else str(a) for a in author])
        return str(author)
    return ""

def wrap_text(text, max_chars=32):
    if not text: return []
    words = text.split()
    lines = []
    curr = ""
    for w in words:
        if len(curr) + (1 if curr else 0) + len(w) <= max_chars:
            curr += (" " if curr else "") + w
        else:
            if curr: lines.append(curr)
            curr = w
    if curr: lines.append(curr)
    return lines

def find_serif_font(bold=True):
    candidates = [
        "/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf" if bold else "/usr/share/fonts/gsfonts/NimbusRoman-Regular.otf",
        "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/gsfonts/C059-Bold.otf" if bold else "/usr/share/fonts/gsfonts/C059-Regular.otf",
        "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSerif.ttf"
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None

def wrap_text_font(draw, text, font, max_width):
    if not text:
        return []
    words = text.split()
    lines = []
    curr = ""
    for w in words:
        test = f"{curr} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w_px = bbox[2] - bbox[0]
        if w_px <= max_width:
            curr = test
        else:
            if curr:
                lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
    return lines

def find_markdown_metadata(base_dir, target_input):
    """
    Única fonte de verdade para metadados de capa:
    1. content/books/**/*.md (Livros e E-books)
    2. content/articles/**/*.md (Artigos Acadêmicos)
    Suporta caminhos diretos, caminhos relativos ou slugs simples.
    """
    base_path = Path(base_dir)
    target_path = Path(target_input)
    
    # 1. Verificação de caminho direto (relativo ao cwd ou base_dir)
    candidates = [
        target_path,
        base_path / target_path,
        target_path.with_suffix(".md"),
        (base_path / target_path).with_suffix(".md")
    ]
    for c in candidates:
        if c.is_file():
            c_resolved = c.resolve()
            books_dir = (base_path / "content" / "books").resolve()
            articles_dir = (base_path / "content" / "articles").resolve()
            if str(c_resolved).startswith(str(books_dir)):
                return parse_markdown_file(str(c_resolved)).get("metadata", {}), True, c.stem
            elif str(c_resolved).startswith(str(articles_dir)):
                return parse_markdown_file(str(c_resolved)).get("metadata", {}), False, c.stem

    # 2. Busca recursiva em content/books e content/articles por slug
    stem = target_path.stem
    patterns = [f"{stem}.md", stem.replace("_", "-") + ".md", stem.replace("-", "_") + ".md"]
    
    for pat in patterns:
        for p in (base_path / "content" / "books").rglob(pat):
            if p.is_file():
                return parse_markdown_file(str(p)).get("metadata", {}), True, p.stem
        for p in (base_path / "content" / "articles").rglob(pat):
            if p.is_file():
                return parse_markdown_file(str(p)).get("metadata", {}), False, p.stem
                
    return {}, False, stem

def inject_cover_text(base_dir, raw_image_path, custom_text=None, target_slug=None):
    import re
    from PIL import ImageDraw, ImageFont, ImageFilter

    img_path = Path(raw_image_path).resolve()
    if not img_path.exists():
        print(f"❌ Erro: Arquivo de imagem não encontrado em: {img_path}")
        return
        
    base_name = target_slug or re.sub(r"^\.?tmp_raw_", "", img_path.stem)
    file_name = img_path.name
    
    title, subtitle, authors, date = "", "", "", ""
    is_book = False
    
    originals_dir = Path(base_dir) / 'assets' / 'covers' / 'originals'
    originals_dir.mkdir(parents=True, exist_ok=True)
    dest_path = originals_dir / f"{base_name}.png"
    
    if custom_text:
        parts = [s.strip() for s in custom_text.split('|')]
        title = parts[0] if len(parts) > 0 else ""
        if len(parts) > 1 and ":" not in title and len(parts) > 3:
            subtitle = parts[1]
            authors = parts[2]
            date = parts[3]
        else:
            authors = parts[1] if len(parts) > 1 else ""
            date = parts[2] if len(parts) > 2 else ""
        is_book = not bool(date)
    else:
        metadata, is_book, canonical_slug = find_markdown_metadata(base_dir, base_name)
        if metadata:
            base_name = canonical_slug
            dest_path = originals_dir / f"{base_name}.png"
            title = metadata.get('title', base_name)
            authors = extract_authors(metadata)
            date = format_date(metadata.get('date'))
        else:
            print(f"⚠️ Aviso: Markdown correspondente não encontrado em content/books nem em content/articles. Usando nome do arquivo como título.")
            title = base_name.replace('-', ' ').replace('_', ' ').title()

    # Split title and subtitle if colon is present
    if not subtitle and ":" in title:
        parts = title.split(":", 1)
        title = parts[0].strip()
        subtitle = parts[1].strip()

    print(f"🎨 Compondo tipografia editorial na capa:\n   Título   : {title}\n   Subtítulo: {subtitle or '(Nenhum)'}\n   Autor(es): {authors}\n   Tipo     : {'E-book / Livro' if is_book else 'Artigo'}")
    
    width, height = 1696, 2528
    originals_dir = Path(base_dir) / 'assets' / 'covers' / 'originals'
    originals_dir.mkdir(parents=True, exist_ok=True)
    dest_path = originals_dir / f"{base_name}.png"
    
    try:
        with Image.open(img_path) as img:
            img = img.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
            
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw_shadow = ImageDraw.Draw(shadow)
        
        bold_font_path = find_serif_font(bold=True)
        reg_font_path = find_serif_font(bold=False) or bold_font_path
        
        # Determine font sizes adapted for 1696x2528 canvas
        title_len = len(title)
        title_fs = 175 if title_len < 16 else (135 if title_len < 32 else 105)
        title_font = ImageFont.truetype(bold_font_path, title_fs) if bold_font_path else ImageFont.load_default()
        
        subtitle_fs = 140 if subtitle and len(subtitle) < 25 else 115
        subtitle_font = ImageFont.truetype(reg_font_path, subtitle_fs) if (reg_font_path and subtitle) else None
        
        author_fs = 120
        author_font = ImageFont.truetype(reg_font_path, author_fs) if (reg_font_path and authors) else None
        
        date_fs = 68
        date_font = ImageFont.truetype(reg_font_path, date_fs) if (reg_font_path and date) else None
        
        start_y = 260
        curr_y = start_y
        
        # Render Main Title (Matte Gold: #E2C974)
        title_lines = wrap_text_font(draw, title, title_font, max_width=1450)
        line_spacing = int(title_fs * 1.22)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) // 2
            draw_shadow.text((x + 4, curr_y + 5), line, font=title_font, fill=(0, 0, 0, 220))
            draw.text((x, curr_y), line, font=title_font, fill=(226, 201, 116, 255))
            curr_y += line_spacing
            
        curr_y += 25
        
        # Render Subtitle (Crisp White: #FFFFFF)
        if subtitle and subtitle_font:
            sub_lines = wrap_text_font(draw, subtitle, subtitle_font, max_width=1450)
            sub_spacing = int(subtitle_fs * 1.25)
            for line in sub_lines:
                bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                line_w = bbox[2] - bbox[0]
                x = (width - line_w) // 2
                draw_shadow.text((x + 3, curr_y + 4), line, font=subtitle_font, fill=(0, 0, 0, 210))
                draw.text((x, curr_y), line, font=subtitle_font, fill=(255, 255, 255, 255))
                curr_y += sub_spacing
            curr_y += 30
            
        # Render Author (Title Case Crisp White: #F8FAFC)
        if authors and author_font:
            curr_y += 20
            author_text = authors.title() if authors.isupper() else authors
            bbox = draw.textbbox((0, 0), author_text, font=author_font)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) // 2
            draw_shadow.text((x + 3, curr_y + 4), author_text, font=author_font, fill=(0, 0, 0, 210))
            draw.text((x, curr_y), author_text, font=author_font, fill=(248, 250, 252, 255))
            
        # Render Date (if Article, centered at bottom)
        if not is_book and date and date_font:
            date_y = height - 190
            bbox = draw.textbbox((0, 0), date, font=date_font)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) // 2
            draw_shadow.text((x + 3, date_y + 3), date, font=date_font, fill=(0, 0, 0, 200))
            draw.text((x, date_y), date, font=date_font, fill=(203, 213, 225, 240))
            
        # Blur shadow slightly for natural depth
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Composite final artwork
        final_img = Image.alpha_composite(img, shadow)
        final_img = Image.alpha_composite(final_img, overlay).convert("RGB")
        final_img.save(dest_path, format="PNG", quality=95)
        
        print(f"✅ Capa com tipografia vetorial gerada em: {dest_path}")
        
        if img_path != dest_path and img_path.exists() and img_path.parent == Path(base_dir) / 'assets' / 'covers':
            img_path.unlink()
            print(f"🧹 Imagem temporária removida de: assets/covers/{file_name}")
            
    except Exception as e:
        print(f"❌ Erro ao injetar texto na capa: {e}")

