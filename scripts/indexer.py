import os
import json
import subprocess
import time
from pathlib import Path
from scripts.utils import parse_markdown_file, is_draft, parse_date_to_timestamp, estimate_reading_time, remove_empty_keys, get_files_recursively, slugify
from scripts.categories import derive_udc_from_categories
from scripts.identity_registry import (
    IdentityRegistry,
    IdentityViolationError,
    REGISTRY_RELATIVE_PATH,
    ScannedDocument,
    compute_body_sha256,
    extract_primary_author,
    validate_registry_snapshot_with_sqlite,
)

GITHUB_USERNAME = 'HelenoSalgado'
REPO_NAME = 'openscimd'
DEFAULT_WPM = 200
SOURCE_EXT_PRIORITY = ['.pdf', '.html', '.md', '.txt', '.docx']


def _resolve_summary(metadata, body, existing=None):
    summary = metadata.get('summary') or metadata.get('sumary') or ''
    if not summary and existing:
        summary = existing.get('summary', '')
    if not summary:
        clean_body = "\n".join([line for line in body.split('\n') if not line.strip().startswith('#')]).strip()
        first_p = clean_body.split('\n\n')[0] if clean_body else ''
        summary = first_p[:250].strip() + ('...' if len(first_p) > 250 else '')
    return summary


def _resolve_source_pdf_url(base_dir, base_name):
    source_candidates = list((Path(base_dir) / 'assets' / 'sources').glob(f"{base_name}.*"))
    if not source_candidates:
        return None
    source_candidates.sort(
        key=lambda p: SOURCE_EXT_PRIORITY.index(p.suffix.lower()) if p.suffix.lower() in SOURCE_EXT_PRIORITY else 999
    )
    ext = source_candidates[0].suffix
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/sources/{base_name}{ext}"


def update_articles_index(base_dir, registry=None):
    print('🔄 Iniciando atualização do index-articles.json...')
    articles_dir = Path(base_dir) / 'content' / 'articles'
    index_file = Path(base_dir) / 'index-articles.json'

    if not articles_dir.exists():
        print(f"⚠️ Diretório de artigos não encontrado em: {articles_dir}")
        return []

    own_registry = registry is None
    if own_registry:
        registry = IdentityRegistry.load(base_dir)

    existing_index = {'repo_name': 'OpenSciMD', 'type': 'articles', 'last_updated': 0, 'articles': []}
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                existing_index = json.load(f)
        except Exception:
            pass

    existing_map = {}
    for art in existing_index.get('articles', []):
        if 'remote_url' in art:
            filename = art['remote_url'].split('/')[-1]
            existing_map[filename] = art
            if '/main/content/articles/' in art['remote_url']:
                rel = art['remote_url'].split('/main/content/articles/')[-1]
                existing_map[rel] = art

    scanned_records = []
    scanned_docs = []
    for filepath in get_files_recursively(articles_dir):
        file_path = Path(filepath)
        rel_path = file_path.relative_to(articles_dir).as_posix()
        file_name = file_path.name
        base_name = file_path.stem

        parsed = parse_markdown_file(str(file_path))
        metadata, body = parsed['metadata'], parsed['body']
        existing = existing_map.get(rel_path) or existing_map.get(file_name)
        draft_flag = is_draft(metadata)
        if draft_flag:
            print(f"⚠️ Rascunho preservado no ledger sem publicação: {rel_path}")

        title = metadata.get('title') or (existing.get('title') if existing else base_name)
        primary_author = extract_primary_author(metadata, existing)
        date_ts = parse_date_to_timestamp(metadata.get('date')) if metadata.get('date') else None
        created_hint = date_ts or (existing.get('published_at') if existing else None) or int(file_path.stat().st_mtime * 1000)

        doc = ScannedDocument(
            rel_path=rel_path,
            title=str(title),
            author=primary_author,
            doi=metadata.get('doi') or metadata.get('DOI'),
            body=body,
            body_sha256=compute_body_sha256(body),
            is_draft=draft_flag,
            created_hint_ms=created_hint,
        )
        scanned_docs.append(doc)
        if not draft_flag:
            scanned_records.append((file_path, rel_path, base_name, metadata, body, existing, doc))

    id_by_rel = registry.reconcile_kind('art', scanned_docs, 'articles')
    if own_registry:
        registry.save()

    updated_articles = []
    for file_path, rel_path, base_name, metadata, body, existing, doc in scanned_records:
        print(f"📄 Processando artigo: {rel_path}")
        art_id = id_by_rel[rel_path]
        title = doc.title

        authors_list = metadata.get('authors')
        author = metadata.get('author')
        if not authors_list and not author and existing:
            authors_list = existing.get('authors')
            author = existing.get('author')

        summary = _resolve_summary(metadata, body, existing)
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/content/articles/{rel_path}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/covers/mobile/{base_name}.webp"
        pdf_url = _resolve_source_pdf_url(base_dir, base_name)

        categories = metadata.get('categories') or metadata.get('category') or (existing.get('categories') if existing else [])
        if isinstance(categories, str): categories = [categories]

        published_at = doc.created_hint_ms

        est_time = estimate_reading_time(body, DEFAULT_WPM)

        journal_name = metadata.get('journal') or (existing.get('journal') if existing else None)
        volume_val = metadata.get('volume') if metadata.get('volume') is not None else (existing.get('volume') if existing else None)
        journal_id = f"journal_{slugify(journal_name)}" if journal_name else None
        volume_id = f"vol_{slugify(journal_name)}_{volume_val}" if journal_name and volume_val is not None else None

        udc_code = metadata.get('udc') or metadata.get('UDC')
        if not udc_code:
            udc_code = derive_udc_from_categories(categories)

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
            'udc': udc_code,
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

    articles_changed = (existing_index.get('articles') != updated_articles)
    if articles_changed or existing_index.get('last_updated', 0) == 0:
        existing_index['last_updated'] = int(time.time() * 1000)
    existing_index['articles'] = updated_articles

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(existing_index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-articles.json atualizado com sucesso! ({len(updated_articles)} artigos indexados)")
    return updated_articles


def update_books_index(base_dir, registry=None):
    print('🔄 Iniciando atualização do index-books.json...')
    books_dir = Path(base_dir) / 'content' / 'books'
    index_file = Path(base_dir) / 'index-books.json'

    if not books_dir.exists():
        print(f"⚠️ Diretório de livros não encontrado em: {books_dir}")
        return []

    own_registry = registry is None
    if own_registry:
        registry = IdentityRegistry.load(base_dir)

    existing_index = {'repo_name': 'OpenSciMD', 'type': 'books', 'last_updated': 0, 'books': []}
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                existing_index = json.load(f)
        except Exception:
            pass

    existing_map = {}
    for book in existing_index.get('books', []):
        if 'remote_url' in book:
            rel_path = book['remote_url'].split('/main/content/books/')[-1]
            existing_map[rel_path] = book

    scanned_records = []
    scanned_docs = []
    for filepath in get_files_recursively(books_dir):
        file_path = Path(filepath)
        rel_path = file_path.relative_to(books_dir).as_posix()
        base_name = file_path.stem

        parsed = parse_markdown_file(str(file_path))
        metadata, body = parsed['metadata'], parsed['body']
        existing = existing_map.get(rel_path)
        draft_flag = is_draft(metadata)
        if draft_flag:
            print(f"⚠️ Rascunho preservado no ledger sem publicação: {rel_path}")

        title = metadata.get('title') or (existing.get('title') if existing else base_name)
        primary_author = extract_primary_author(metadata, existing)
        date_ts = parse_date_to_timestamp(metadata.get('date')) if metadata.get('date') else None
        created_hint = date_ts or (existing.get('published_at') if existing else None) or int(file_path.stat().st_mtime * 1000)

        doc = ScannedDocument(
            rel_path=rel_path,
            title=str(title),
            author=primary_author,
            doi=metadata.get('doi') or metadata.get('DOI'),
            body=body,
            body_sha256=compute_body_sha256(body),
            is_draft=draft_flag,
            created_hint_ms=created_hint,
        )
        scanned_docs.append(doc)
        if not draft_flag:
            scanned_records.append((file_path, rel_path, base_name, metadata, body, existing, doc))

    id_by_rel = registry.reconcile_kind('book', scanned_docs, 'books')
    if own_registry:
        registry.save()

    updated_books = []
    for file_path, rel_path, base_name, metadata, body, existing, doc in scanned_records:
        print(f"📚 Processando livro: {rel_path}")
        book_id = id_by_rel[rel_path]
        title = doc.title

        authors_list = metadata.get('authors')
        author = metadata.get('author')
        if not authors_list and not author and existing:
            authors_list = existing.get('authors')
            author = existing.get('author')

        summary = _resolve_summary(metadata, body, existing)
        remote_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/content/books/{rel_path}"
        cover_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/assets/covers/mobile/{base_name}.webp"
        pdf_url = _resolve_source_pdf_url(base_dir, base_name)

        categories = metadata.get('categories') or metadata.get('category') or (existing.get('categories') if existing else [])
        if isinstance(categories, str): categories = [categories]

        published_at = doc.created_hint_ms

        est_time = estimate_reading_time(body, DEFAULT_WPM)

        udc_code = metadata.get('udc') or metadata.get('UDC')
        if not udc_code:
            udc_code = derive_udc_from_categories(categories)

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
            'udc': udc_code,
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

    books_changed = (existing_index.get('books') != updated_books)
    if books_changed or existing_index.get('last_updated', 0) == 0:
        existing_index['last_updated'] = int(time.time() * 1000)
    existing_index['books'] = updated_books

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

    existing_journals_index = {'repo_name': 'OpenSciMD', 'type': 'journals', 'last_updated': 0, 'journals': []}
    if journals_file.exists():
        try:
            with open(journals_file, 'r', encoding='utf-8') as f:
                existing_journals_index = json.load(f)
        except Exception:
            pass

    journals_changed = (existing_journals_index.get('journals') != journals_list)
    last_updated = existing_journals_index.get('last_updated', 0)
    if journals_changed or last_updated == 0:
        last_updated = int(time.time() * 1000)

    result = {
        'repo_name': 'OpenSciMD',
        'type': 'journals',
        'last_updated': last_updated,
        'journals': journals_list
    }

    with open(journals_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f"✅ index-journals.json atualizado com sucesso! ({len(journals_list)} periódicos indexados)")
    return journals_list

def update_index(base_dir):
    print('🔄 Iniciando atualização geral de índices...')
    registry = IdentityRegistry.load(base_dir)
    articles = update_articles_index(base_dir, registry=registry)
    update_books_index(base_dir, registry=registry)
    registry.save()
    update_journals_index(base_dir, articles)
    print('✅ Todos os índices atualizados com sucesso!')


def validate_catalog_identities(base_dir, git_ref="HEAD"):
    """Valida invariantes do ledger canônico e sincronia com index-*.json."""
    root = Path(base_dir)
    reg_path = root / REGISTRY_RELATIVE_PATH
    if not reg_path.exists():
        print(f"❌ Ledger canônico ausente: {reg_path}")
        return False

    try:
        current = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"❌ Erro ao ler {reg_path}: {exc}")
        return False

    baseline = None
    if (root / ".git").exists():
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "show", f"{git_ref}:{REGISTRY_RELATIVE_PATH.as_posix()}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                baseline = json.loads(proc.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            baseline = None

    try:
        validate_registry_snapshot_with_sqlite(baseline, current)
    except IdentityViolationError as exc:
        print(f"❌ Violação de imutabilidade no ledger: {exc}")
        return False

    entries = current.get("entries", {})
    checks = (
        ("index-articles.json", "articles", "art", "/content/articles/"),
        ("index-books.json", "books", "book", "/content/books/"),
    )
    errors = []
    for json_name, list_key, expected_kind, marker in checks:
        idx_path = root / json_name
        if not idx_path.exists():
            errors.append(f"Arquivo de índice ausente: {json_name}")
            continue
        idx_data = json.loads(idx_path.read_text(encoding="utf-8"))
        seen_ids = set()
        for item in idx_data.get(list_key, []):
            doc_id = item.get("id")
            if not doc_id or doc_id in seen_ids:
                errors.append(f"ID inválido ou duplicado em {json_name}: {doc_id}")
                continue
            seen_ids.add(doc_id)
            entry = entries.get(doc_id)
            if not entry:
                errors.append(f"ID '{doc_id}' em {json_name} não existe no catalog-registry.json.")
                continue
            if entry.get("kind") != expected_kind or entry.get("status") != "active":
                errors.append(
                    f"ID '{doc_id}' em {json_name} está com status='{entry.get('status')}' no ledger."
                )
            remote_url = str(item.get("remote_url") or "")
            rel = remote_url.split(marker)[-1] if marker in remote_url else ""
            if rel and entry.get("current_rel_path") != rel:
                errors.append(
                    f"ID '{doc_id}' em {json_name} aponta para '{rel}', mas o ledger aponta para '{entry.get('current_rel_path')}'."
                )

        for entry_id, entry in entries.items():
            if entry.get("kind") == expected_kind and entry.get("status") == "active" and entry_id not in seen_ids:
                errors.append(f"Entrada ativa '{entry_id}' do ledger ausente em {json_name}.")

    if errors:
        for err in errors:
            print(f"❌ {err}")
        return False

    print(
        f"✅ Ledger de IDs íntegro ({len(entries)} entradas; high-water art={current['sequences']['art']}, book={current['sequences']['book']})."
    )
    return True


