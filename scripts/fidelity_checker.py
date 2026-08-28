import os
import time
import difflib

# Adia o import do transformers para não atrasar o CLI caso o comando não seja usado
def get_models():
    from transformers import MarianMTModel, MarianTokenizer
    
    print("Carregando modelo MarianMT (EN -> PT)...")
    tokenizer_en_pt = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tc-big-en-pt")
    model_en_pt = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-tc-big-en-pt")
    
    print("Carregando modelo MarianMT (PT -> EN) para Tradução Reversa...")
    tokenizer_pt_en = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ROMANCE-en")
    model_pt_en = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ROMANCE-en")
    
    return tokenizer_en_pt, model_en_pt, tokenizer_pt_en, model_pt_en

def translate(text, tokenizer, model, prefix=""):
    # Alguns modelos MarianMT exigem o prefixo do idioma destino, ex: ">>por<<"
    # Para o ROMANCE-en o destino é inglês, o inglês é o padrão.
    # Para tc-big-en-pt o destino é português.
    full_text = prefix + text if prefix else text
    inputs = tokenizer(full_text, return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def test_fidelity(english_text, custom_pt_translation=None):
    from scripts.text_tools import Colors
    
    start_load = time.time()
    tokenizer_en_pt, model_en_pt, tokenizer_pt_en, model_pt_en = get_models()
    load_time = time.time() - start_load
    
    print(f"\n{Colors.HEADER}=== TESTE DE FIDELIDADE (Back-Translation) ==={Colors.ENDC}")
    print(f"Modelos carregados em {load_time:.2f}s na CPU.\n")
    
    print(f"{Colors.BLUE}Texto Original (Inglês):{Colors.ENDC} {english_text}")
    
    if custom_pt_translation:
        pt_text = custom_pt_translation
        print(f"{Colors.YELLOW}Tradução Fornecida (Para Análise):{Colors.ENDC} {pt_text}")
    else:
        start_trans = time.time()
        pt_text = translate(english_text, tokenizer_en_pt, model_en_pt)
        trans_time = time.time() - start_trans
        print(f"{Colors.GREEN}Tradução do MarianMT (EN->PT) [{trans_time:.2f}s]:{Colors.ENDC} {pt_text}")
        
    start_back = time.time()
    # O modelo ROMANCE-en precisa do prefixo >>en<< ou detecta sozinho.
    # A documentação oficial diz para colocar o target language no começo.
    back_translated = translate(pt_text, tokenizer_pt_en, model_pt_en, prefix=">>en<< ")
    back_time = time.time() - start_back
    
    print(f"{Colors.RED}Tradução Reversa (PT->EN) [{back_time:.2f}s]:{Colors.ENDC} {back_translated}")
    
    # Calcular similaridade simples por palavras usando difflib
    seq = difflib.SequenceMatcher(None, english_text.lower().split(), back_translated.lower().split())
    sim = seq.ratio()
    print(f"\n{Colors.BOLD}Taxa de Preservação Semântica (Simples): {sim:.2%}{Colors.ENDC}")
    
    if sim > 0.65:
        print(f"Resultado: {Colors.GREEN}✅ Tradução Fiel detectada.{Colors.ENDC}")
    elif sim > 0.40:
        print(f"Resultado: {Colors.YELLOW}⚠️ Tradução Mediana / Paráfrase detectada.{Colors.ENDC}")
    else:
        print(f"Resultado: {Colors.RED}❌ Tradução Alucinada ou Pobre detectada.{Colors.ENDC}")
