import os
import json
import time
from pathlib import Path
from scripts.utils import parse_markdown_file, is_draft, parse_date_to_timestamp, estimate_reading_time, remove_empty_keys, get_files_recursively

GITHUB_USERNAME = 'HelenoSalgado'
REPO_NAME = 'openscimd'
DEFAULT_WPM = 200

def update_articles_index(base_dir):
    print('🔄 Iniciando atualização do index-articles.json...')
    articles_dir = Path(base_dir) / 'articles'
    index_file = Path(base_dir) / 'index-articles.json'
    
    if not articles_dir.exists():
        print(f"⚠️ Diretório de artigos não encontrado em: {articles_dir}")
        return
        
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
        if 'id' in art and str(art['id']).startswith('art_'):
            num = int(art['id'][4:])
            if num > max_id_num: max_id_num = num
            
    updated_articles = []
    for filepath in get_files_recursively(articles_dir):
        file_path = Path(filepath)
        file_name = file_path.name
        base_name = file_path.stem
        
        parsed = parse_markdown_file(str(file_path))
        metadata, body = parsed['metadata'], parsed['body']
        
        if is_draft(metadata):
            print(f"⚠️ Ignorando rascunho: {file_name}")
            continue
            
        print(f"📄 Processando artigo: {file_name}")
        existing = existing_map.get(file_name)
        
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
            
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/articles/{file_name}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/covers/mobile/{base_name}.webp"
        
        pdf_url = None
        if (Path(base_dir) / 'pdfs' / f"{base_name}.pdf").exists():
            pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/pdfs/{base_name}.pdf"
            
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
            'journal': metadata.get('journal'),
            'volume': metadata.get('volume'),
            'issue': metadata.get('issue'),
            'pages': metadata.get('pages'),
            'language': metadata.get('language')
        }
        updated_articles.append(remove_empty_keys(entry))
        
    existing_index['articles'] = updated_articles
    existing_index['last_updated'] = int(time.time() * 1000)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(existing_index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-articles.json atualizado com sucesso! ({len(updated_articles)} artigos indexados)")

def update_books_index(base_dir):
    print('🔄 Iniciando atualização do index-books.json...')
    books_dir = Path(base_dir) / 'books'
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
            rel_path = book['remote_url'].split('/main/books/')[-1]
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
            
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/books/{rel_path}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/covers/mobile/{base_name}.webp"
        
        pdf_url = None
        if (Path(base_dir) / 'pdfs' / f"{base_name}.pdf").exists():
            pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/pdfs/{base_name}.pdf"
            
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

def update_index(base_dir):
    print('🔄 Iniciando atualização geral de índices...')
    update_articles_index(base_dir)
    update_books_index(base_dir)
    print('✅ Todos os índices atualizados com sucesso!')
