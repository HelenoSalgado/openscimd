import os
import re
import json
from pathlib import Path

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
        regex_pattern = rf'\b({books_pattern})\s+(\d+)[:.,](\d+)\b'
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
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def load_dict(dict_path):
    if os.path.exists(dict_path):
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_dict(dict_path, d):
    with open(dict_path, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted(d.items())), f, indent=4, ensure_ascii=False)

def match_case(original, new_word):
    if original.isupper(): return new_word.upper()
    elif original.istitle(): return new_word.capitalize()
    return new_word

def get_line_number(content, index):
    return content.count('\n', 0, index) + 1

def spellcheck(filepath, dict_path=None):
    if not os.path.exists(filepath):
        print(f"{Colors.RED}Erro: Arquivo '{filepath}' não encontrado.{Colors.ENDC}")
        return
        
    if not dict_path:
        dict_path = os.path.join(os.path.dirname(__file__), "dicionario_arcaico.json")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    body_start_idx = 0
    frontmatter_match = re.match(r'^---\n.*?\n---\n', content, re.DOTALL)
    if frontmatter_match:
        body_start_idx = frontmatter_match.end()

    dictionary = load_dict(dict_path)
    if not dictionary:
        print(f"{Colors.YELLOW}Dicionário {dict_path} está vazio ou não existe.{Colors.ENDC}")
    
    words = list(re.finditer(r'\b[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*\b', content[body_start_idx:]))
    
    replacements = []
    replace_all = set()
    ignore_all = set()
    
    pending_matches = []
    for m in words:
        word = m.group(0).lower()
        if word in dictionary:
            pending_matches.append({
                "original": m.group(0),
                "lower": word,
                "real_start": m.start() + body_start_idx,
                "real_end": m.end() + body_start_idx
            })
            
    total_matches = len(pending_matches)
    
    if total_matches == 0:
        print(f"{Colors.GREEN}Nenhuma palavra do dicionário de arcaísmos encontrada no texto. Tudo limpo!{Colors.ENDC}")
        return
        
    print(f"{Colors.HEADER}{Colors.BOLD}=== Revisão Ortográfica (Dicionário Manual) ==={Colors.ENDC}")
    print(f"Arquivo: {filepath}")
    print(f"Encontrados {Colors.YELLOW}{total_matches}{Colors.ENDC} arcaísmos mapeados.\n")
    
    current_match = 0
    for match in pending_matches:
        original = match["original"]
        lower_orig = match["lower"]
        real_start = match["real_start"]
        real_end = match["real_end"]
        
        if lower_orig in ignore_all: continue
            
        replacement = match_case(original, dictionary[lower_orig])
        
        if lower_orig in replace_all:
            replacements.append((real_start, real_end, replacement))
            continue
            
        current_match += 1
        line_num = get_line_number(content, real_start)
        
        context_start = max(body_start_idx, real_start - 60)
        context_end = min(len(content), real_end + 60)
        
        prefix = content[context_start:real_start].replace('\n', ' ')
        suffix = content[real_end:context_end].replace('\n', ' ')
        highlighted_word = f"{Colors.RED}{Colors.BOLD}{original}{Colors.ENDC}"
        
        print("-" * 60)
        print(f"{Colors.BLUE}[{current_match}/{total_matches}] Linha {line_num}{Colors.ENDC}")
        print(f"Contexto: ...{prefix}{highlighted_word}{suffix}...")
        print(f"Substituir {Colors.RED}{original}{Colors.ENDC} por {Colors.GREEN}{Colors.BOLD}{replacement}{Colors.ENDC}?")
        
        while True:
            print(f"Opções: [{Colors.GREEN}s{Colors.ENDC}]im / [{Colors.RED}n{Colors.ENDC}]ão / [{Colors.GREEN}t{Colors.ENDC}]odas / [{Colors.RED}i{Colors.ENDC}]gnorar todas / [{Colors.YELLOW}e{Colors.ENDC}]ditar / [{Colors.BLUE}q{Colors.ENDC}]uit")
            choice = input("> ").lower().strip()
            if choice in ['s', 'n', 't', 'i', 'e', 'q']:
                break
            print("Opção inválida.")
            
        if choice == 'q':
            print(f"\n{Colors.YELLOW}Revisão interrompida.{Colors.ENDC}")
            print("Deseja salvar as substituições feitas até agora? [s/n]")
            if input("> ").lower().strip() != 's':
                print("Alterações descartadas.")
                return
            break
        elif choice == 's':
            replacements.append((real_start, real_end, replacement))
        elif choice == 't':
            replace_all.add(lower_orig)
            replacements.append((real_start, real_end, replacement))
        elif choice == 'i':
            ignore_all.add(lower_orig)
        elif choice == 'e':
            custom = input(f"Digite a nova palavra para substituir '{original}': ")
            replacements.append((real_start, real_end, match_case(original, custom)))
            print(f"Deseja salvar '{lower_orig}' -> '{custom.lower()}' no dicionário permanentemente? [s/n]")
            if input("> ").lower().strip() == 's':
                dictionary[lower_orig] = custom.lower()
                save_dict(dict_path, dictionary)
                print(f"{Colors.GREEN}Dicionário atualizado!{Colors.ENDC}")
                
    if not replacements:
        print(f"\n{Colors.YELLOW}Nenhuma substituição foi confirmada.{Colors.ENDC}")
        return
        
    for start, end, new_word in reversed(replacements):
        content = content[:start] + new_word + content[end:]
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"\n{Colors.GREEN}{Colors.BOLD}Revisão salva! {len(replacements)} modificações feitas no arquivo.{Colors.ENDC}")
