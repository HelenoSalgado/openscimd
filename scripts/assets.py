import os
from pathlib import Path
from PIL import Image

SCREEN_SIZES = {
    'mobile': 480,
    'tablet': 768,
    'desktop': 1200
}

def convert_assets(base_dir: str):
    assets_dir = Path(base_dir) / 'assets' / 'images'
    print(f'🖼️  Iniciando a conversão de assets em: {assets_dir}')
    
    if not assets_dir.exists():
        print(f"Erro: Diretório {assets_dir} não encontrado.")
        return
        
    originals_dir = assets_dir / 'originals'
    originals_dir.mkdir(parents=True, exist_ok=True)
    
    for size in SCREEN_SIZES.keys():
        (assets_dir / size).mkdir(parents=True, exist_ok=True)
        
    image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    
    for item in assets_dir.iterdir():
        if item.is_file() and item.suffix.lower() in image_exts:
            item.rename(originals_dir / item.name)
            print(f"📦 Mapeado original para pasta originals: {item.name}")
            
    processed = 0
    for file in originals_dir.iterdir():
        if file.is_file() and file.suffix.lower() in image_exts:
            output_name = f"{file.stem}.webp"
            print(f"\n⏳ Processando imagem: {file.name}")
            
            try:
                with Image.open(file) as img:
                    orig_w, orig_h = img.size
                    for size_name, target_w in SCREEN_SIZES.items():
                        output_path = assets_dir / size_name / output_name
                        print(f"   -> Convertendo para {size_name} ({target_w}px)...")
                        
                        if orig_w > target_w:
                            ratio = target_w / orig_w
                            new_size = (target_w, int(orig_h * ratio))
                            resized = img.resize(new_size, Image.Resampling.LANCZOS)
                        else:
                            resized = img.copy()
                            
                        resized.save(output_path, format="WEBP", quality=85)
                        print(f"   ✅ Salvo em: assets/{size_name}/{output_name}")
                processed += 1
            except Exception as e:
                print(f"   ❌ Erro ao converter {file.name}: {e}")
                
    print(f"\n🎉 Processamento concluído! {processed} imagens originais processadas para todos os tamanhos.")
