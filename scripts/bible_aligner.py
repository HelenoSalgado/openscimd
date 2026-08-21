import re
import os
from scripts.fidelity_checker import get_models, translate
from scripts.text_tools import Colors
from tqdm import tqdm
import difflib

def parse_english_raw(filepath):
    """Parses English file with **C:V** format."""
    verses = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = re.compile(r'\*\*(\d+):(\d+)\*\*\s*(.*?)(?=\*\*(\d+):(\d+)\*\*|$)', re.DOTALL)
    for match in pattern.finditer(content):
        ch = match.group(1)
        vs = match.group(2)
        text = match.group(3).strip()
        text = re.sub(r'\s+', ' ', text) # normalize spaces
        verses[f"{ch}:{vs}"] = text
        
    return verses

def parse_portuguese_review(filepath):
    """Parses Portuguese file with ## Capítulo X and ¹ ² format."""
    verses = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_chapter = 0
    superscript_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    
    # Regex para pegar número sobrescrito no início da linha
    verse_pattern = re.compile(r'^([⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s*(.*)')
    
    for line in lines:
        line = line.strip()
        # Procura mudança de capítulo
        chap_match = re.search(r'## Capítulo (\d+)', line)
        if chap_match:
            current_chapter = chap_match.group(1)
            continue
            
        # Tenta extrair versículo sobrescrito
        v_match = verse_pattern.match(line)
        if v_match and current_chapter:
            v_num = v_match.group(1).translate(superscript_map)
            text = v_match.group(2).strip()
            verses[f"{current_chapter}:{v_num}"] = text
            
    return verses

def parse_portuguese_draft(filepath):
    """Parses Portuguese file with ## Capítulo X and 1. 2. format."""
    verses = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_chapter = 0
    
    verse_pattern = re.compile(r'^(\d+)\.\s*(.*)')
    
    for line in lines:
        line = line.strip()
        chap_match = re.search(r'## Capítulo (\d+)', line)
        if chap_match:
            current_chapter = chap_match.group(1)
            continue
            
        v_match = verse_pattern.match(line)
        if v_match and current_chapter:
            v_num = v_match.group(1)
            text = v_match.group(2).strip()
            verses[f"{current_chapter}:{v_num}"] = text
            
    return verses

