import re
import yaml
import requests
from pathlib import Path

def enrich_metadata(filepath: str):
    """Enriquece metadados YAML do Markdown consultando DOI no Crossref."""
    path = Path(filepath)
    if not path.exists():
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        print("Frontmatter YAML não encontrado no arquivo.")
        return
        
    fm_text, body = match.group(1), match.group(2)
    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        print(f"Erro ao parsear YAML: {e}")
        return
        
    doi = meta.get('DOI') or meta.get('doi')
    if not doi:
        print("Nenhum DOI encontrado no Frontmatter.")
        return
        
    print(f"Buscando metadados para o DOI: {doi} via Crossref...")
    url = f"https://api.crossref.org/works/{doi}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()['message']
        
        # Extrair e enriquecer metadados
        if 'publisher' in data and not meta.get('journal'):
            meta['journal'] = data['publisher']
            
        if 'volume' in data and not meta.get('volume'):
            meta['volume'] = data['volume']
            
        if 'issue' in data and not meta.get('issue'):
            meta['issue'] = data['issue']
            
        if 'page' in data and not meta.get('pages'):
            meta['pages'] = data['page']
            
        if 'ISSN' in data and len(data['ISSN']) > 0 and not meta.get('e_issn'):
            meta['e_issn'] = data['ISSN'][0]
            
        if 'author' in data and not meta.get('authors'):
            authors = []
            for a in data['author']:
                author_dict = {"name": f"{a.get('given', '')} {a.get('family', '')}".strip()}
                if 'ORCID' in a:
                    author_dict['orcid'] = a['ORCID'].split('/')[-1]
                if 'affiliation' in a and len(a['affiliation']) > 0:
                    author_dict['affiliation'] = a['affiliation'][0].get('name', '')
                authors.append(author_dict)
            meta['authors'] = authors
            if 'author' in meta:
                del meta['author'] # Prefer authors array

        new_fm_text = yaml.dump(meta, sort_keys=False, allow_unicode=True)
        new_content = f"---\n{new_fm_text}---\n{body}"
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Metadados enriquecidos com sucesso!")
        
    except requests.RequestException as e:
        print(f"Erro ao buscar na API Crossref: {e}")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
