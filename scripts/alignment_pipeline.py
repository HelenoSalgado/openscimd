import os
import re
import tempfile
from pathlib import Path
from tqdm import tqdm
import difflib
from scripts.fidelity_checker import get_models, translate
from scripts.text_tools import Colors

def extract_clean_text(filepath):
    """
    Função universal que extrai o texto puro de um Markdown (Bíblia, artigos, livros),
    limpando frontmatter, cabeçalhos, marcações de versículos e formatação Markdown,
    retornando uma lista de parágrafos/linhas para comparação 1-para-1.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Remover YAML frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    # Forçar quebra de linha antes de marcadores KJV inline (ex: **1:2**)
    content = re.sub(r'\s+(\*\*\d+:\d+\*\*)', r'\n\1', content)
    
    lines = content.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Ignorar linhas vazias, headers, separadores e citações blockquote
        if not line or line.startswith('#') or line.startswith('---') or line.startswith('>'):
            continue
            
        # Limpar marcadores de versículos estilo KJV (**1:1**)
        line = re.sub(r'\*\*\d+:\d+\*\*\s*', '', line)
        
        # Limpar marcadores de versículos no início da linha (ex: "1. ", "14. ", "¹ ", "¹² ")
        line = re.sub(r'^([⁰¹²³⁴⁵⁶⁷⁸⁹]+|\d+\.)\s*', '', line)
        
        # Limpar negrito e itálico do markdown
        line = re.sub(r'[*_]{1,3}', '', line)
        
        # Limpar links markdown [texto](link)
        line = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', line)
        
        line = line.strip()
        if len(line) > 3: # Ignora detritos muito curtos
            clean_lines.append(line)
            
    return clean_lines


def run_alignment_and_report(raw_en_file, pt_file, limit=None, start=None, end=None):
    output_report = os.path.splitext(pt_file)[0] + "-revisao.md"
    
    print(f"[{Colors.BLUE}Universal Extractor{Colors.ENDC}] Limpando e extraindo (EN): {raw_en_file}...")
    en_verses = extract_clean_text(raw_en_file)
    
    print(f"[{Colors.BLUE}Universal Extractor{Colors.ENDC}] Limpando e extraindo (PT): {pt_file}...")
    pt_verses = extract_clean_text(pt_file)
    
    start_idx = max(0, start - 1) if start is not None else 0
    if end is not None:
        end_idx = end
    elif limit is not None:
        end_idx = start_idx + limit
    else:
        end_idx = None
        
    if end_idx is not None:
        en_verses = en_verses[start_idx:end_idx]
        pt_verses = pt_verses[start_idx:end_idx]
    elif start_idx > 0:
        en_verses = en_verses[start_idx:]
        pt_verses = pt_verses[start_idx:]
    
    # Define current start index for display purposes
    current_start_idx = start_idx
        
    # Salvar em arquivos temporários
    temp_dir = tempfile.mkdtemp(prefix="openscimd_")
    temp_en = os.path.join(temp_dir, "temp_en.txt")
    temp_pt = os.path.join(temp_dir, "temp_pt.txt")
    
    with open(temp_en, 'w', encoding='utf-8') as f:
        f.write("\n".join(en_verses))
        
    with open(temp_pt, 'w', encoding='utf-8') as f:
        f.write("\n".join(pt_verses))
        
    print(f"{Colors.YELLOW}Textos limpos exportados para: {temp_dir}{Colors.ENDC}")
    
    min_len = min(len(en_verses), len(pt_verses))
    diff = abs(len(en_verses) - len(pt_verses))
    
    if min_len == 0:
        print(f"{Colors.RED}Erro: Não foi possível extrair texto comparável dos arquivos.{Colors.ENDC}")
        return
        
    if diff > 0:
        print(f"{Colors.RED}Aviso de Desalinhamento Crítico: O arquivo EN tem {len(en_verses)} blocos e o PT tem {len(pt_verses)} blocos. Isso comprometerá a precisão a partir do desalinhamento.{Colors.ENDC}")
        
    print(f"{Colors.GREEN}Iniciando análise de {min_len} parágrafos simultâneos. Carregando MarianMT...{Colors.ENDC}")
    _, _, tokenizer_pt_en, model_pt_en = get_models()
    
    report_lines = []
    report_lines.append(f"# Relatório Universal de Revisão (Alinhamento Semântico)\n")
    report_lines.append(f"- **Origem (EN):** `{os.path.basename(raw_en_file)}` ({len(en_verses)} blocos)")
    report_lines.append(f"- **Destino (PT):** `{os.path.basename(pt_file)}` ({len(pt_verses)} blocos)")
    report_lines.append(f"- **Total Comparado (1-para-1):** {min_len}\n")
    if diff > 0:
        report_lines.append(f"> ⚠️ **ALERTA:** Diferença estrutural de {diff} parágrafos identificada. Os blocos podem estar dessincronizados.\n")
    
    suspicious_count = 0
    
    # Lê dos arquivos temporários linha a linha
    with open(temp_en, 'r', encoding='utf-8') as fen, open(temp_pt, 'r', encoding='utf-8') as fpt:
        for idx, (en_line, pt_line) in tqdm(enumerate(zip(fen, fpt)), total=min_len, desc="Avaliando Textos"):
            en_text = en_line.strip()
            pt_text = pt_line.strip()
            
            back_translated = translate(pt_text, tokenizer_pt_en, model_pt_en, prefix=">>en<< ")
            
            seq = difflib.SequenceMatcher(None, en_text.lower(), back_translated.lower())
            sim = seq.ratio()
            
            status = "✅ Fiel"
            if sim < 0.50:
                status = "❌ Alerta Crítico"
                suspicious_count += 1
            elif sim < 0.70:
                status = "⚠️ Paráfrase ou Omissão"
                suspicious_count += 1
                
            report_lines.append(f"### Bloco {current_start_idx + idx + 1} - {status} ({sim:.1%})")
            report_lines.append(f"**Original (EN):** {en_text}\n")
            report_lines.append(f"**Tradução (PT):** {pt_text}\n")
            report_lines.append(f"**Reversa (EN):** {back_translated}\n")
            report_lines.append("---\n")
        
    report_lines.insert(5 if diff > 0 else 4, f"- **Avisos Disparados:** {suspicious_count}\n")
    
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"\n{Colors.GREEN}Relatório de revisão finalizado: {output_report}{Colors.ENDC}")

