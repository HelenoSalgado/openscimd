import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from scripts.utils import parse_markdown_file
from scripts.covers import inject_cover_text, find_markdown_metadata

def get_env(base_dir):
    env_path = Path(base_dir) / '.env'
    if not env_path.exists():
        print('❌ Arquivo .env não localizado! Copie .env.example para .env')
        return {}
    load_dotenv(dotenv_path=env_path)
    return os.environ

def generate_cover(base_dir, article_name, custom_style=None, provider="gemini"):
    env = get_env(base_dir)
    
    metadata, is_book, canonical_slug = find_markdown_metadata(base_dir, article_name)
    if not metadata:
        print(f"❌ Documento Markdown correspondente não encontrado em content/books nem em content/articles para: {article_name}")
        return
        
    base_name = canonical_slug
    cover_dest = Path(base_dir) / 'assets' / 'covers' / f"{base_name}.png"
        
    summary = metadata.get('summary', '')
    title = metadata.get('title', base_name)
    categories = metadata.get('categories', [])
    categories_str = ", ".join(categories) if isinstance(categories, list) else str(categories)
    
    summary_text = f'Core philosophical and theological themes: "{summary}". ' if summary else ''
    cat_text = f'Categories: {categories_str}. ' if categories_str else ''
    
    base_prompt = (
        f"Masterpiece fine-art conceptual background artwork for an academic { 'book / treatise' if is_book else 'scholarly article' }, vertical 2:3 aspect ratio (portrait orientation). "
        f"Aesthetic: High-end intellectual academic publishing house (Penguin Classics, Oxford World's Classics, Gallimard). "
        f"Style: Moody, abstract fine-art oil painting with heavy canvas texture, minimalist chiaroscuro, and deep obsidian, midnight navy, charcoal, and dark lapis tones with subtle burnished matte gold accents. "
        f"Subject: A profound, mature, and subtle metaphysical abstraction representing the core intellectual thesis of: \"{title}\". "
        f"{summary_text}"
        f"{cat_text}"
        f"Keep the upper third balanced and suitable for high-end typography overlay. Keep the entire bottom area calm and uncluttered. "
        f"Strictly NO text, NO letters, NO words, NO titles, NO borders, NO frames, NO literal light beams, NO lamps, NO books on tables, NO human figures, and NO religious depictions of Jesus Christ."
    )
                   
    final_prompt = f"{base_prompt} Specific visual nuances: {custom_style}." if custom_style else base_prompt
    
    if provider == "gemini":
        api_key = env.get('IA_KEY')
        if not api_key:
            print("❌ Erro: Chave IA_KEY não preenchida no .env")
            return
            
        model_name = env.get('IA_MODEL_NAME', 'gemini-3.1-flash-image')
        print(f"🎨 Modelo de IA: {model_name}\n⏳ Enviando requisição conceitual para o Google Gemini...")
        
        client = genai.Client(api_key=api_key)
        try:
            result = client.models.generate_images(
                model=model_name,
                prompt=final_prompt,
                config=genai.types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/png",
                )
            )
            
            if not result.generated_images:
                print("❌ Nenhuma imagem retornada pelo Gemini.")
                return
                
            img_bytes = result.generated_images[0].image.image_bytes
            
            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cover_dest.parent / f".tmp_raw_{base_name}.png"
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
                
            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(temp_path), target_slug=base_name)
            
        except Exception as e:
            print(f"❌ Erro na geração Gemini: {e}")
            
    elif provider == "openai":
        api_key = env.get('IA_KEY')
        api_url = env.get('IA_API_URL')
        model_name = env.get('IA_MODEL_NAME')
        if not api_key or not api_url:
            print("❌ Erro: IA_KEY ou IA_API_URL não preenchidas no .env")
            return
            
        print(f"🎨 Modelo de IA (OpenAI API): {model_name or 'Padrão'}\n⏳ Enviando requisição conceitual...")
        try:
            resp = requests.post(api_url, headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }, json={
                'model': model_name,
                'prompt': final_prompt,
                'n': 1,
                'size': '1024x1024',
                'response_format': 'url'
            })
            resp.raise_for_status()
            data = resp.json()
            url = data.get('data', [{}])[0].get('url') or data.get('url') or data.get('image')
            b64 = data.get('data', [{}])[0].get('b64_json')
            
            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cover_dest.parent / f".tmp_raw_{base_name}.png"
            if url:
                img_data = requests.get(url).content
                with open(temp_path, 'wb') as f: f.write(img_data)
            elif b64:
                with open(temp_path, 'wb') as f: f.write(base64.b64decode(b64))
            
            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(temp_path), target_slug=base_name)
        except Exception as e:
            print(f"❌ Erro API: {e}")
            
    elif provider == "agy":
        import shutil
        import subprocess
        import time
        
        agy_bin = shutil.which("agy")
        if not agy_bin:
            print("❌ Erro: CLI 'agy' não foi encontrada no PATH do sistema.")
            return
            
        print("🎨 Provedor: Antigravity CLI (agy)\n⏳ Acionando agy para geração de imagem conceitual...")
        start_time = time.time() - 5
        
        raw_slug = base_name.replace('-', '_')
        prompt_instruction = (
            f"Gere uma imagem conceitual de capa na proporção '2:3' com o ImageName '{raw_slug}_raw' "
            f"utilizando a ferramenta generate_image com o seguinte prompt estrito em inglês:\n\n{final_prompt}"
        )
        
        try:
            res = subprocess.run(
                [agy_bin, "--dangerously-skip-permissions", "-p", prompt_instruction],
                capture_output=True,
                text=True,
                check=False
            )
            
            brain_dir = Path.home() / ".gemini" / "antigravity-cli" / "brain"
            found_img = None
            
            search_slugs = {
                base_name,
                base_name.replace('-', '_'),
                base_name.replace('_', '-'),
                raw_slug,
                f"{raw_slug}_raw",
                f"{base_name}_raw"
            }
            
            candidates = []
            if brain_dir.exists():
                for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                    for img_p in brain_dir.rglob(ext):
                        if any(slug in img_p.stem for slug in search_slugs):
                            candidates.append(img_p)
                            
            # Fallback em busca local
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                for img_p in Path(base_dir).rglob(ext):
                    if any(slug in img_p.stem for slug in search_slugs):
                        candidates.append(img_p)
                        
            if candidates:
                # Prioriza os gerados após o início da execução, ordenados por mtime mais recente
                recent = [c for c in candidates if c.stat().st_mtime >= start_time]
                if recent:
                    recent.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    found_img = recent[0]
                else:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    found_img = candidates[0]
                    
            if not found_img:
                print("❌ Não foi possível localizar a imagem gerada pelo agy.")
                if res.stderr:
                    print(f"   Log agy: {res.stderr}")
                return
                
            print(f"📦 Arte conceitual recuperada: {found_img.name}")
            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            target_cover_path = cover_dest.parent / f"{base_name}.png"
            shutil.copy2(found_img, target_cover_path)
            
            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(target_cover_path), target_slug=base_name)
            
        except Exception as e:
            print(f"❌ Erro na integração com agy: {e}")

