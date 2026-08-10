import os
import re
import subprocess
from pathlib import Path
import yaml

def convert_html_to_md(base_dir, input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)
    if not input_path.exists():
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Convertendo '{input_file}' para '{output_file}'...")
    
    cmd = [
        "pandoc", "-f", "html", "-t", "markdown_strict+yaml_metadata_block-raw_html",
        "--markdown-headings=atx", "--standalone", "--wrap=none",
        str(input_path), "-o", str(output_path)
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Ocorreu um erro durante a conversão do pandoc.")
        return
        
    print("Mapeando frontmatter YAML para o padrão openscimd...")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    meta = {}
    body = content
    
    if match:
        fm_text, body = match.group(1), match.group(2)
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
        f.write(new_fm + body)
        
    print(f"Conversão e mapeamento concluídos com sucesso! Arquivo salvo em: {output_path}")
