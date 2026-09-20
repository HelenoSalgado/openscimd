import os
import json
import time
from pathlib import Path
from scripts.utils import parse_markdown_file, is_draft, parse_date_to_timestamp, estimate_reading_time, remove_empty_keys, get_files_recursively, slugify

GITHUB_USERNAME = 'HelenoSalgado'
REPO_NAME = 'openscimd'
DEFAULT_WPM = 200

def update_articles_index(base_dir):
    print('🔄 Iniciando atualização do index-articles.json...')
    articles_dir = Path(base_dir) / 'content' / 'articles'
    index_file = Path(base_dir) / 'index-articles.json'
    
    if not articles_dir.exists():
        print(f"⚠️ Diretório de artigos não encontrado em: {articles_dir}")
        return []
        
    existing_index = {'repo_name': 'OpenSciMD', 'type': 'articles', 'last_updated': 0, 'articles': []}
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                existing_index = json.load(f)
        except Exception:
            pass
            
    existing_map = {}
    max_id_num = 0
    for art in existing_index.get('articles', []):
        if 'remote_url' in art:
            filename = art['remote_url'].split('/')[-1]
            existing_map[filename] = art
            if '/main/content/articles/' in art['remote_url']:
                rel = art['remote_url'].split('/main/content/articles/')[-1]
                existing_map[rel] = art
        if 'id' in art and str(art['id']).startswith('art_'):
            num = int(art['id'][4:])
            if num > max_id_num: max_id_num = num
            
    updated_articles = []
    for filepath in get_files_recursively(articles_dir):
        file_path = Path(filepath)
        rel_path = file_path.relative_to(articles_dir).as_posix()
        file_name = file_path.name
        base_name = file_path.stem
        
        parsed = parse_markdown_file(str(file_path))
        metadata, body = parsed['metadata'], parsed['body']
        
        if is_draft(metadata):
            print(f"⚠️ Ignorando rascunho: {rel_path}")
            continue
            
        print(f"📄 Processando artigo: {rel_path}")
        existing = existing_map.get(rel_path) or existing_map.get(file_name)
        
        art_id = existing.get('id') if existing else None
        if not art_id:
            max_id_num += 1
            art_id = f"art_{str(max_id_num).zfill(3)}"
            
        title = metadata.get('title') or (existing.get('title') if existing else base_name)
        
        authors_list = metadata.get('authors')
        author = metadata.get('author')
        if not authors_list and not author and existing:
            authors_list = existing.get('authors')
            author = existing.get('author')
            
        summary = metadata.get('summary') or metadata.get('sumary') or ''
        if not summary and existing: summary = existing.get('summary', '')
        if not summary:
            clean_body = "\n".join([line for line in body.split('\n') if not line.strip().startswith('#')]).strip()
            first_p = clean_body.split('\n\n')[0] if clean_body else ''
            summary = first_p[:250].strip() + ('...' if len(first_p) > 250 else '')
            
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/content/articles/{rel_path}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/covers/mobile/{base_name}.webp"
        
        pdf_url = None
        if (Path(base_dir) / 'assets' / 'pdfs' / f"{base_name}.pdf").exists():
            pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/pdfs/{base_name}.pdf"
            
        categories = metadata.get('categories') or metadata.get('category') or (existing.get('categories') if existing else [])
        if isinstance(categories, str): categories = [categories]
        
        published_at = existing.get('published_at') if existing else None
        if metadata.get('date'):
            ts = parse_date_to_timestamp(metadata.get('date'))
            if ts: published_at = ts
        if not published_at:
            published_at = int(file_path.stat().st_mtime * 1000)
            
        est_time = estimate_reading_time(body, DEFAULT_WPM)

        journal_name = metadata.get('journal') or (existing.get('journal') if existing else None)
        volume_val = metadata.get('volume') if metadata.get('volume') is not None else (existing.get('volume') if existing else None)
        journal_id = f"journal_{slugify(journal_name)}" if journal_name else None
        volume_id = f"vol_{slugify(journal_name)}_{volume_val}" if journal_name and volume_val is not None else None
        
        entry = {
            'id': art_id,
            'title': title,
            'author': author,
            'authors': authors_list,
            'summary': summary,
            'remote_url': remote_url,
            'cover_url': cover_url,
            'pdf_url': pdf_url,
            'categories': categories,
            'published_at': published_at,
            'estimated_reading_time_min': est_time,
            'doi': metadata.get('doi') or metadata.get('DOI'),
            'udc': metadata.get('udc') or metadata.get('UDC'),
            'bbk': metadata.get('bbk') or metadata.get('BBK'),
            'hos': metadata.get('hos') or metadata.get('HoS'),
            'license': metadata.get('license') or metadata.get('licence'),
            'journal': journal_name,
            'journal_id': journal_id,
            'volume': str(volume_val) if volume_val is not None else None,
            'volume_id': volume_id,
            'issue': str(metadata.get('issue')) if metadata.get('issue') is not None else None,
            'pages': str(metadata.get('pages')) if metadata.get('pages') is not None else None,
            'language': metadata.get('language'),
            'e_issn': metadata.get('e_issn') or metadata.get('E_ISSN') or metadata.get('e-issn'),
            'issn': metadata.get('issn') or metadata.get('ISSN')
        }
        updated_articles.append(remove_empty_keys(entry))
        
    existing_index['articles'] = updated_articles
    existing_index['last_updated'] = int(time.time() * 1000)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(existing_index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-articles.json atualizado com sucesso! ({len(updated_articles)} artigos indexados)")
    return updated_articles

def update_books_index(base_dir):
    print('🔄 Iniciando atualização do index-books.json...')
    books_dir = Path(base_dir) / 'content' / 'books'
    index_file = Path(base_dir) / 'index-books.json'
    
    if not books_dir.exists():
        print(f"⚠️ Diretório de livros não encontrado em: {books_dir}")
        return
        
    existing_index = {'repo_name': 'OpenSciMD', 'type': 'books', 'last_updated': 0, 'books': []}
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                existing_index = json.load(f)
        except Exception:
            pass
            
    existing_map = {}
    max_id_num = 0
    for book in existing_index.get('books', []):
        if 'remote_url' in book:
            rel_path = book['remote_url'].split('/main/content/books/')[-1]
            existing_map[rel_path] = book
        if 'id' in book and str(book['id']).startswith('book_'):
            num = int(book['id'][5:])
            if num > max_id_num: max_id_num = num
            
    updated_books = []
    for filepath in get_files_recursively(books_dir):
        file_path = Path(filepath)
        rel_path = file_path.relative_to(books_dir).as_posix()
        file_name = file_path.name
        base_name = file_path.stem
        
        parsed = parse_markdown_file(str(file_path))
        metadata, body = parsed['metadata'], parsed['body']
        
        if is_draft(metadata):
            print(f"⚠️ Ignorando rascunho: {rel_path}")
            continue
            
        print(f"📚 Processando livro: {rel_path}")
        existing = existing_map.get(rel_path)
        
        book_id = existing.get('id') if existing else None
        if not book_id:
            max_id_num += 1
            book_id = f"book_{str(max_id_num).zfill(3)}"
            
        title = metadata.get('title') or (existing.get('title') if existing else base_name)
        
        authors_list = metadata.get('authors')
        author = metadata.get('author')
        if not authors_list and not author and existing:
            authors_list = existing.get('authors')
            author = existing.get('author')
            
        summary = metadata.get('summary') or metadata.get('sumary') or ''
        if not summary and existing: summary = existing.get('summary', '')
        if not summary:
            clean_body = "\n".join([line for line in body.split('\n') if not line.strip().startswith('#')]).strip()
            first_p = clean_body.split('\n\n')[0] if clean_body else ''
            summary = first_p[:250].strip() + ('...' if len(first_p) > 250 else '')
            
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/content/books/{rel_path}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/covers/mobile/{base_name}.webp"
        
        pdf_url = None
        if (Path(base_dir) / 'assets' / 'pdfs' / f"{base_name}.pdf").exists():
            pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/pdfs/{base_name}.pdf"
            
        categories = metadata.get('categories') or metadata.get('category') or (existing.get('categories') if existing else [])
        if isinstance(categories, str): categories = [categories]
        
        published_at = existing.get('published_at') if existing else None
        if metadata.get('date'):
            ts = parse_date_to_timestamp(metadata.get('date'))
            if ts: published_at = ts
        if not published_at:
            published_at = int(file_path.stat().st_mtime * 1000)
            
        est_time = estimate_reading_time(body, DEFAULT_WPM)
        
        entry = {
            'id': book_id,
            'title': title,
            'author': author,
            'authors': authors_list,
            'summary': summary,
            'remote_url': remote_url,
            'cover_url': cover_url,
            'pdf_url': pdf_url,
            'categories': categories,
            'published_at': published_at,
            'estimated_reading_time_min': est_time,
            'license': metadata.get('license') or metadata.get('licence'),
            'language': metadata.get('language'),
            'originalLanguage': metadata.get('originalLanguage'),
            'translator': metadata.get('translator'),
            'edition': metadata.get('edition'),
            'isbn': metadata.get('isbn')
        }
        updated_books.append(remove_empty_keys(entry))
        
    existing_index['books'] = updated_books
    existing_index['last_updated'] = int(time.time() * 1000)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(existing_index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-books.json atualizado com sucesso! ({len(updated_books)} livros indexados)")
    return updated_books

def update_journals_index(base_dir, articles=None):
    print('🔄 Iniciando atualização do index-journals.json...')
    articles_file = Path(base_dir) / 'index-articles.json'
    journals_file = Path(base_dir) / 'index-journals.json'
    
    if articles is None:
        if not articles_file.exists():
            print(f"⚠️ {articles_file} não encontrado para gerar índice de periódicos.")
            return
        try:
            with open(articles_file, 'r', encoding='utf-8') as f:
                articles = json.load(f).get('articles', [])
        except Exception as e:
            print(f"❌ Erro ao ler {articles_file}: {e}")
            return

    journals_map = {}
    for art in articles:
        journal_name = art.get('journal')
        if not journal_name:
            continue
            
        j_slug = slugify(journal_name)
        if j_slug not in journals_map:
            journals_map[j_slug] = {
                'id': f"journal_{j_slug}",
                'name': journal_name,
                'slug': j_slug,
                'e_issn': art.get('e_issn'),
                'issn': art.get('issn'),
                'volumes_map': {}
            }
        else:
            if not journals_map[j_slug].get('e_issn') and art.get('e_issn'):
                journals_map[j_slug]['e_issn'] = art.get('e_issn')
            if not journals_map[j_slug].get('issn') and art.get('issn'):
                journals_map[j_slug]['issn'] = art.get('issn')
                
        volume_val = str(art.get('volume', '1'))
        v_map = journals_map[j_slug]['volumes_map']
        if volume_val not in v_map:
            year = None
            if art.get('published_at'):
                year = time.gmtime(art['published_at'] / 1000).tm_year
            v_map[volume_val] = {
                'id': f"vol_{j_slug}_{volume_val}",
                'volume': volume_val,
                'year': year,
                'issues_map': {}
            }
            
        issue_val = str(art.get('issue', '1'))
        iss_map = v_map[volume_val]['issues_map']
        if issue_val not in iss_map:
            iss_map[issue_val] = {
                'issue': issue_val,
                'articles': []
            }
        iss_map[issue_val]['articles'].append(art['id'])

    journals_list = []
    for j_slug, j_data in sorted(journals_map.items(), key=lambda x: x[1]['name']):
        volumes_list = []
        total_arts = 0
        for v_val, v_data in sorted(j_data['volumes_map'].items(), key=lambda x: (int(x[0]) if x[0].isdigit() else str(x[0]))):
            issues_list = []
            for iss_val, iss_data in sorted(v_data['issues_map'].items(), key=lambda x: (int(x[0]) if x[0].isdigit() else str(x[0]))):
                issues_list.append({
                    'issue': iss_data['issue'],
                    'articles': iss_data['articles']
                })
                total_arts += len(iss_data['articles'])
            volumes_list.append({
                'id': v_data['id'],
                'volume': v_data['volume'],
                'year': v_data['year'],
                'issues': issues_list
            })
            
        journal_entry = {
            'id': j_data['id'],
            'name': j_data['name'],
            'slug': j_data['slug'],
            'e_issn': j_data['e_issn'],
            'issn': j_data['issn'],
            'total_articles': total_arts,
            'volumes': volumes_list
        }
        journals_list.append(remove_empty_keys(journal_entry))

    result = {
        'repo_name': 'OpenSciMD',
        'type': 'journals',
        'last_updated': int(time.time() * 1000),
        'journals': journals_list
    }

    with open(journals_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-journals.json atualizado com sucesso! ({len(journals_list)} periódicos indexados)")
    return journals_list

def update_index(base_dir):
    print('🔄 Iniciando atualização geral de índices...')
    articles = update_articles_index(base_dir)
    update_books_index(base_dir)
    update_journals_index(base_dir, articles)
    print('✅ Todos os índices atualizados com sucesso!')

