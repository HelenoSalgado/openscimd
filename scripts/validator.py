import os
from pathlib import Path
from scripts.utils import parse_markdown_file, parse_date_to_timestamp

def validate_articles(base_dir):
    print('🧪 Iniciando validação de formato e metadados dos artigos...\n')
    articles_dir = Path(base_dir) / 'content' / 'articles'
    covers_dir = Path(base_dir) / 'assets' / 'covers'
    pdfs_dir = Path(base_dir) / 'assets' / 'pdfs'
    
    if not articles_dir.exists():
        print(f"❌ Diretório de artigos não encontrado em: {articles_dir}")
        return False
        
    invalid_count = 0
    total_errors = 0
    total_warnings = 0
    
    for file in articles_dir.glob('*.md'):
        errors, warnings = [], []
        base_name = file.stem
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.startswith('---'):
                errors.append('O arquivo não inicia com delimitadores de metadados ("---").')
                
            parsed = parse_markdown_file(str(file))
            metadata = parsed['metadata']
            
            if not metadata.get('title') or not str(metadata.get('title')).strip():
                errors.append('Campo obrigatório "title" está ausente ou vazio.')
                
            has_author = bool(metadata.get('author') and str(metadata.get('author')).strip())
            has_authors = bool(metadata.get('authors') and isinstance(metadata.get('authors'), list) and metadata.get('authors'))
            if not has_author and not has_authors:
                errors.append('Campo de autoria obrigatório ("author" ou "authors") ausente ou vazio.')
                
            summary = metadata.get('summary') or metadata.get('sumary')
            if not summary or not str(summary).strip():
                errors.append('Resumo ("summary" ou "sumary") ausente ou vazio.')
            elif metadata.get('sumary'):
                warnings.append('Encontrado erro de digitação no campo "sumary". Recomenda-se renomear para "summary".')
                
            if not metadata.get('date'):
                errors.append('Campo obrigatório "date" ausente.')
            else:
                ts = parse_date_to_timestamp(metadata.get('date'))
                if not ts:
                    errors.append(f'Formato de data inválido: "{metadata.get("date")}". Use YYYY-MM-DD ou DD-MM-YYYY.')
                    
            license_ = metadata.get('license') or metadata.get('licence')
            if not license_ or not str(license_).strip():
                errors.append('Campo de licença obrigatório ("license" ou "licence") ausente ou vazio.')
            elif metadata.get('licence'):
                warnings.append('Chave de licença escrita como "licence". Recomenda-se padronizar para "license".')
                
            if not metadata.get('doi') and not metadata.get('DOI'):
                warnings.append('Campo recomendado "DOI" está ausente.')
            if not metadata.get('udc') and not metadata.get('UDC'):
                warnings.append('Campo recomendado "UDC" está ausente.')
            if not metadata.get('bbk') and not metadata.get('BBK'):
                warnings.append('Campo recomendado "BBK" está ausente.')
            if not metadata.get('categories') and not metadata.get('category'):
                warnings.append('Campo recomendado "categories" ou "category" está ausente.')
            if not metadata.get('journal'):
                warnings.append('Campo administrativo "journal" está ausente.')
                
            if not (covers_dir / 'mobile' / f"{base_name}.webp").exists():
                warnings.append(f'Imagem de capa mobile correspondente não localizada em assets/covers/mobile/{base_name}.webp.')
                
            if not (pdfs_dir / f"{base_name}.pdf").exists():
                warnings.append(f'Arquivo original em PDF não localizado em assets/pdfs/{base_name}.pdf.')
                
        except Exception as e:
            errors.append(f'Falha crítica ao ler/processar arquivo: {e}')
            
        if errors or warnings:
            print(f"📄 Artigo: {file.name}")
            if errors:
                invalid_count += 1
                total_errors += len(errors)
                for err in errors: print(f"  ❌ [ERRO] {err}")
            if warnings:
                total_warnings += len(warnings)
                for warn in warnings: print(f"  ⚠️ [ALERTA] {warn}")
            print("")
            
    print('-' * 50)
    print(f"📊 Resumo da Validação:")
    print(f"   - Artigos Verificados: {len(list(articles_dir.glob('*.md')))}")
    print(f"   - Artigos com Erros Fatais: {invalid_count}")
    print(f"   - Total de Erros: {total_errors}")
    print(f"   - Total de Alertas: {total_warnings}\n")
    
    if invalid_count > 0:
        print('❌ Falha na validação! Corrija os erros listados.')
        return False
    else:
        print('✅ Validação concluída com sucesso! Todos os artigos estão aptos.')
        return True
