import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from scripts.utils import parse_markdown_file
from scripts.covers import inject_cover_text

def get_env(base_dir):
    env_path = Path(base_dir) / '.env'
    if not env_path.exists():
        print('❌ Arquivo .env não localizado! Copie .env.example para .env')
        return {}
    load_dotenv(dotenv_path=env_path)
    return os.environ

def generate_cover(base_dir, article_name, custom_style=None, provider="gemini"):
    env = get_env(base_dir)
    base_name = Path(article_name).stem
    article_path = Path(base_dir) / 'articles' / f"{base_name}.md"
    cover_dest = Path(base_dir) / 'covers' / f"{base_name}.png"
    
    if not article_path.exists():
        print(f"❌ Artigo não encontrado em: {article_path}")
        return
        
    parsed = parse_markdown_file(str(article_path))
    metadata = parsed['metadata']
    summary = metadata.get('summary', '')
    title = metadata.get('title', base_name)
    
    summary_text = f'Themes description: "{summary}". ' if summary else ''
    base_prompt = (f"Create a clean, minimalist book cover background artwork with vertical 2:3 aspect ratio (portrait orientation). "
                   f"The illustration must NOT be abstract; instead, depict a clear, solid, recognizable minimalist object or symbol representing the single strongest central element of the following academic paper: \"{title}\". "
                   f"{summary_text}"
                   f"The main subject must be perfectly centered in the middle of the composition. "
                   f"Keep ample clean negative space at the top and bottom of the image for editorial text placement. "
                   f"Use a professional, elegant academic color scheme with 2D flat vector aesthetic. "
                   f"Strictly NO text, NO letters, NO words, NO titles, NO borders, and NO writing anywhere on the image. High-quality cover illustration.")
                   
    final_prompt = f"{base_prompt} Visual style requested: {custom_style}." if custom_style else base_prompt
    
    if provider == "gemini":
        api_key = env.get('IA_KEY')
        if not api_key:
            print("❌ Erro: Chave IA_KEY não preenchida no .env")
            return
            
        model_name = env.get('IA_MODEL_NAME', 'gemini-3.1-flash-image')
        print(f"🎨 Modelo de IA: {model_name}\n⏳ Enviando requisição para o Google Gemini...")
        
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
            temp_path = cover_dest.parent / f"{base_name}.png"
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
                
            print("🎨 Aplicando overlay de tipografia editorial...")
            inject_cover_text(base_dir, str(temp_path))
            
        except Exception as e:
            print(f"❌ Erro na geração Gemini: {e}")
            
    elif provider == "openai":
        api_key = env.get('IA_KEY')
        api_url = env.get('IA_API_URL')
        model_name = env.get('IA_MODEL_NAME')
        if not api_key or not api_url:
            print("❌ Erro: IA_KEY ou IA_API_URL não preenchidas no .env")
            return
            
        print(f"🎨 Modelo de IA (OpenAI API): {model_name or 'Padrão'}\n⏳ Enviando requisição...")
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
            temp_path = cover_dest.parent / f"{base_name}.png"
            if url:
                img_data = requests.get(url).content
                with open(temp_path, 'wb') as f: f.write(img_data)
            elif b64:
                with open(temp_path, 'wb') as f: f.write(base64.b64decode(b64))
            
            print("🎨 Aplicando overlay de tipografia editorial...")
            inject_cover_text(base_dir, str(temp_path))
        except Exception as e:
            print(f"❌ Erro API: {e}")
