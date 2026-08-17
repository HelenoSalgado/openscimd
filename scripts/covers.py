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

def inject_cover_text(base_dir, raw_image_path, custom_text=None):
    img_path = Path(raw_image_path).resolve()
    if not img_path.exists():
        print(f"❌ Erro: Arquivo de imagem não encontrado em: {img_path}")
        return
        
    base_name = img_path.stem
    file_name = img_path.name
    
    title, authors, date = "", "", ""
    collection_name = "COLEÇÃO OPENSCIMD"
    
    if custom_text:
        parts = [s.strip() for s in custom_text.split('|')]
        title = parts[0] if len(parts) > 0 else ""
        authors = parts[1] if len(parts) > 1 else ""
        date = parts[2] if len(parts) > 2 else ""
    else:
        article_path = Path(base_dir) / 'content' / 'articles' / f"{base_name}.md"
        if article_path.exists():
            print(f"📖 Extraindo metadados de: content/articles/{base_name}.md...")
            parsed = parse_markdown_file(str(article_path))
            metadata = parsed['metadata']
            title = metadata.get('title', base_name)
            authors = extract_authors(metadata)
            date = format_date(metadata.get('date'))
        else:
            print(f"⚠️ Aviso: Artigo não encontrado. Usando o nome da imagem como título.")
            title = base_name.replace('-', ' ').upper()
            
    print(f"🎨 Injetando texto na capa:\n   Coleção: {collection_name}\n   Título : {title}\n   Autores: {authors}\n   Data   : {date}")
    
    width, height = 1696, 2528
    header_fs, author_fs, date_fs = 42, 48, 36
    title_fs, title_lh, max_chars = 64, 80, 28
    
    if len(title) > 70:
        title_fs, title_lh, max_chars = 56, 70, 32
        
    title_lines = wrap_text(title, max_chars)
    
    originals_dir = Path(base_dir) / 'assets' / 'covers' / 'originals'
    originals_dir.mkdir(parents=True, exist_ok=True)
    dest_path = originals_dir / f"{base_name}.png"
    
    try:
        print('⏳ Renderizando tipografia...')
        resized_base = Path(base_dir) / 'assets' / 'covers' / f".tmp_base_{base_name}.png"
        with Image.open(img_path) as img:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            img.save(resized_base)
            
        cmds = []
        cmds.append(f'-font "Adwaita-Sans" -pointsize {header_fs} -weight Bold -fill "#334155" -gravity North -annotate +0+160 "{collection_name}"')
        cmds.append(f'-stroke "#CBD5E1" -strokewidth 2 -draw "line 648,215 1048,215" -stroke none')
        
        start_y = 310
        for i, line in enumerate(title_lines):
            line_y = start_y + (i * title_lh)
            cmds.append(f'-font "C059-Bold" -pointsize {title_fs} -weight Bold -fill "#0F172A" -gravity North -annotate +0+{line_y} "{line.upper()}"')
            
        if authors:
            cmds.append(f'-stroke "#94A3B8" -strokewidth 3 -draw "line 748,2220 948,2220" -stroke none')
            cmds.append(f'-font "Adwaita-Sans" -pointsize {author_fs} -weight Bold -fill "#0F172A" -gravity South -annotate +0+210 "{authors}"')
        if date:
            cmds.append(f'-font "Adwaita-Sans" -pointsize {date_fs} -fill "#475569" -gravity South -annotate +0+150 "{date}"')
            
        cmd_str = " ".join(cmds)
        full_cmd = f'magick "{resized_base}" {cmd_str} "{dest_path}"'
        subprocess.run(full_cmd, shell=True, check=True)
        
        if resized_base.exists():
            resized_base.unlink()
            
        print(f"\n✅ Capa final com tipografia salva em: {dest_path}")
        
        if img_path != dest_path and img_path.exists() and img_path.parent == Path(base_dir) / 'assets' / 'covers':
            img_path.unlink()
            print(f"🧹 Imagem temporária removida de: assets/covers/{file_name}")
            
    except Exception as e:
        print(f"❌ Erro ao injetar texto na capa: {e}")
