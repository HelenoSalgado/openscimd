import os
import re
import json
from pathlib import Path
from typing import Optional

def converter_versiculos(input_path, output_path):
    """Converte números no início da linha para formato sobrescrito."""
    superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    
    with open(input_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()
        
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for line in lines:
            match = re.match(r'^(\d+)\.\s*(.*)', line)
            if match:
                num_str = match.group(1)
                rest_of_line = match.group(2)
                super_num = num_str.translate(superscript_map)
                f_out.write(f"{super_num} {rest_of_line}\n")
            else:
                f_out.write(line)
    
    print(f"Conversão de versículos concluída. Escrito em: {output_path}")

from scripts.biblical_books import BIBLE_BOOKS

def normalize_biblical_refs(filepath, target_sep='.', regex_pattern=None, replacement=None):
    """Padroniza referências bíblicas em um documento usando Expressões Regulares seguras."""
    import os, re
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if not regex_pattern:
        books_pattern = '|'.join(BIBLE_BOOKS)
        regex_pattern = rf'\b({books_pattern})\.?\s+(\d+)[:.,]\s*(\d+)\b'
        replacement = rf'\1 \2{target_sep}\3'
        
    try:
        new_content, count = re.subn(regex_pattern, replacement, content, flags=re.IGNORECASE)
    except re.error as e:
        print(f"Erro na expressão regular: {e}")
        return
    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Referências normalizadas: {count} substituições realizadas em '{filepath}'.")
    else:
        print(f"Nenhuma correspondência encontrada para o padrão no arquivo.")

class Colors:
    """ANSI color codes for terminal formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def spellcheck(filepath: str | Path, dict_path: Optional[str | Path] = None) -> None:
    """Revisor ortográfico para arcaísmos (delega para scripts.spellchecker)."""
    from scripts.spellchecker import review_path
    review_path(filepath, dict_path=dict_path)
