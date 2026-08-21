import os
import re
import subprocess
from pathlib import Path
import yaml
import tempfile
import urllib.parse
from bs4 import BeautifulSoup

def preprocess_html_frames(input_path):
    with open(input_path, 'rb') as f:
        # Usamos bs4 com um parser tolerante
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    frames = soup.find_all(['frame', 'iframe'])
    if not frames:
        return str(input_path), None
        
    print(f"Foram encontrados {len(frames)} frames/iframes. Tentando mesclar seus conteúdos...")
    
    combined_soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
    body = combined_soup.body
    
    base_dir = input_path.parent
    
    for frame in frames:
        src = frame.get('src')
        if src:
            if not src.startswith(('http://', 'https://')):
                # Decodifica caminhos URL para caminhos do sistema (ex: %20 -> espaço)
                frame_path = base_dir / urllib.parse.unquote(src)
                if frame_path.exists():
                    try:
                        with open(frame_path, 'rb') as ff:
                            frame_soup = BeautifulSoup(ff.read(), 'html.parser')
                            frame_body = frame_soup.body
                            
                            if frame_body:
                                for child in frame_body.children:
                                    body.append(child)
                            else:
                                for child in frame_soup.children:
                                    body.append(child)
                    except Exception as e:
                        print(f"Aviso: Não foi possível ler o frame {frame_path}: {e}")
                else:
                    print(f"Aviso: Frame local não encontrado: {frame_path}")
            else:
                print(f"Baixando conteúdo do frame externo: {src}")
                import requests
                try:
                    response = requests.get(src, timeout=10)
                    response.raise_for_status()
                    frame_soup = BeautifulSoup(response.content, 'html.parser')
                    frame_body = frame_soup.body
                    if frame_body:
                        for child in frame_body.children:
                            body.append(child)
                    else:
                        for child in frame_soup.children:
                            body.append(child)
                except Exception as e:
                    print(f"Aviso: Falha ao baixar frame externo {src}: {e}")
                
    # Salva o arquivo temporário com os frames mesclados
    temp_fd, temp_path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
        f.write(str(combined_soup))
        
    return temp_path, temp_path

def convert_html_to_md(base_dir, input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return
        
    if output_path.is_dir():
        output_path = output_path / f"{input_path.stem}.md"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Convertendo '{input_file}' para '{output_path}'...")
    
    # Pre-process frames se existirem
    processed_input_path, temp_file_to_cleanup = preprocess_html_frames(input_path)
    
    cmd = [
        "pandoc", "-f", "html", "-t", "markdown_strict+yaml_metadata_block-raw_html",
        "--markdown-headings=atx", "--standalone", "--wrap=none",
        str(processed_input_path), "-o", str(output_path)
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Ocorreu um erro durante a conversão do pandoc.")
    finally:
        if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
            os.remove(temp_file_to_cleanup)
            
    if not output_path.exists():
        return
        
    print("Mapeando frontmatter YAML para o padrão openscimd...")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    meta = {}
    body_text = content
    
    if match:
        fm_text, body_text = match.group(1), match.group(2)
        try:
            parsed_meta = yaml.safe_load(fm_text) or {}
            if isinstance(parsed_meta, dict):
                meta = parsed_meta
        except yaml.YAMLError:
            pass
                    
    title = meta.get('title', 'Sem Título')
    author = meta.get('author', 'Desconhecido')
    summary = meta.get('summary', '')
    date = meta.get('date', '')
    license_ = meta.get('license', 'Domínio público')
    language = meta.get('language', meta.get('lang', 'pt-BR'))
    
    new_fm = f"""---
title: "{title}"
author: "{author}"
summary: "{summary}"
date: "{date}"
license: "{license_}"
language: "{language}"
categories:
  - 
---
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_fm + body_text)
        
    print(f"Conversão e mapeamento concluídos com sucesso! Arquivo salvo em: {output_path}")
