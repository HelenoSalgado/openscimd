import json
import shutil
import tempfile
from pathlib import Path
from scripts.indexer import (
    update_articles_index,
    update_journals_index,
    update_books_index,
    update_index,
    validate_catalog_identities,
)
from scripts.identity_registry import (
    IdentityViolationError,
    REGISTRY_RELATIVE_PATH,
    validate_registry_snapshot_with_sqlite,
)
from scripts.utils import slugify

def test_slugify():
    assert slugify("Peitho / Examina Antiqua") == "peitho-examina-antiqua"
    assert slugify("Revista História da Educação (Online)") == "revista-historia-da-educacao"
    assert slugify("") == "geral"
    assert slugify(None) == "geral"

def test_update_articles_and_journals_index_nested():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        articles_dir = base / 'content' / 'articles' / 'test-journal' / 'vol-1'
        articles_dir.mkdir(parents=True, exist_ok=True)
        
        doc1 = articles_dir / 'article-one.md'
        doc1.write_text(
            '---\n'
            'title: "Artigo de Teste 1"\n'
            'journal: "Revista Teste"\n'
            'volume: 1\n'
            'issue: 1\n'
            'author: "Autor A"\n'
            'date: "2026-01-01"\n'
            'summary: "Resumo do artigo 1"\n'
            '---\n\n'
            '# Introdução\n\nConteúdo do artigo de teste 1.'
        )
        
        doc2 = articles_dir / 'article-two.md'
        doc2.write_text(
            '---\n'
            'title: "Artigo de Teste 2"\n'
            'journal: "Revista Teste"\n'
            'volume: 1\n'
            'issue: 2\n'
            'author: "Autor B"\n'
            'date: "2026-02-01"\n'
            'summary: "Resumo do artigo 2"\n'
            '---\n\n'
            '# Introdução\n\nConteúdo do artigo de teste 2.'
        )
        
        books_dir = base / 'content' / 'books'
        books_dir.mkdir(parents=True, exist_ok=True)
        
        update_index(str(base))
        
        articles_index_path = base / 'index-articles.json'
        assert articles_index_path.exists()
        
        with open(articles_index_path, 'r', encoding='utf-8') as f:
            art_data = json.load(f)
            
        assert len(art_data['articles']) == 2
        assert 'test-journal/vol-1/article-one.md' in art_data['articles'][0]['remote_url']
        assert art_data['articles'][0]['journal_id'] == 'journal_revista-teste'
        assert art_data['articles'][0]['volume_id'] == 'vol_revista-teste_1'
        
        journals_index_path = base / 'index-journals.json'
        assert journals_index_path.exists()
        
        with open(journals_index_path, 'r', encoding='utf-8') as f:
            j_data = json.load(f)
            
        assert len(j_data['journals']) == 1
        j = j_data['journals'][0]
        assert j['id'] == 'journal_revista-teste'
        assert j['name'] == 'Revista Teste'
        assert j['slug'] == 'revista-teste'
        assert j['total_articles'] == 2
        assert len(j['volumes']) == 1
        assert j['volumes'][0]['volume'] == '1'
        assert len(j['volumes'][0]['issues']) == 2

        # Teste de idempotência: executar novamente não deve alterar last_updated nem os arquivos
        first_last_updated = art_data['last_updated']
        first_journal_updated = j_data['last_updated']

        update_index(str(base))

        with open(articles_index_path, 'r', encoding='utf-8') as f:
            art_data_second = json.load(f)
        with open(journals_index_path, 'r', encoding='utf-8') as f:
            j_data_second = json.load(f)

        assert art_data_second['last_updated'] == first_last_updated
        assert j_data_second['last_updated'] == first_journal_updated
        assert art_data_second == art_data
        assert j_data_second == j_data


def test_move_book_and_article_preserves_immutable_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        art_dir = base / 'content' / 'articles' / 'grupo-a'
        book_dir = base / 'content' / 'books' / 'pasta-a'
        art_dir.mkdir(parents=True, exist_ok=True)
        book_dir.mkdir(parents=True, exist_ok=True)

        art_file = art_dir / 'estudo-alfa.md'
        art_file.write_text(
            '---\n'
            'title: "Estudo Alfa Sobre Lógica"\n'
            'author: "Autor Alfa"\n'
            'date: "2026-01-10"\n'
            'summary: "Resumo"\n'
            'pages: "1-10"\n'
            'license: "CC BY 4.0"\n'
            'categories: ["Filosofia"]\n'
            '---\n\n'
            '# Conteúdo Único\n\nTexto estrutural imutável do artigo alfa para rastreio por hash.',
            encoding='utf-8',
        )

        book_file = book_dir / 'tratado-beta.md'
        book_file.write_text(
            '---\n'
            'title: "Tratado Beta"\n'
            'author: "Autor Beta"\n'
            'summary: "Resumo do livro"\n'
            'license: "Domínio Público"\n'
            'categories: ["Filosofia"]\n'
            '---\n\n'
            '# Capítulo I\n\nTexto integral único do tratado beta para preservação de identidade.',
            encoding='utf-8',
        )

        update_index(str(base))
        reg_path = base / REGISTRY_RELATIVE_PATH
        assert reg_path.exists()

        books_v1 = json.loads((base / 'index-books.json').read_text(encoding='utf-8'))['books']
        arts_v1 = json.loads((base / 'index-articles.json').read_text(encoding='utf-8'))['articles']
        assert books_v1[0]['id'] == 'book_001'
        assert arts_v1[0]['id'] == 'art_001'

        # Move os dois arquivos para novas subpastas e novos nomes de arquivo
        new_book_dir = base / 'content' / 'books' / 'autor-beta'
        new_book_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(book_file), str(new_book_dir / 'tratado-beta-revisado.md'))

        new_art_dir = base / 'content' / 'articles' / 'grupo-b'
        new_art_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(art_file), str(new_art_dir / 'estudo-alfa-v2.md'))

        update_index(str(base))

        books_v2 = json.loads((base / 'index-books.json').read_text(encoding='utf-8'))['books']
        arts_v2 = json.loads((base / 'index-articles.json').read_text(encoding='utf-8'))['articles']
        assert len(books_v2) == 1
        assert len(arts_v2) == 1
        assert books_v2[0]['id'] == 'book_001'
        assert arts_v2[0]['id'] == 'art_001'

        registry = json.loads(reg_path.read_text(encoding='utf-8'))
        assert 'pasta-a/tratado-beta.md' in registry['entries']['book_001']['past_rel_paths']
        assert 'grupo-a/estudo-alfa.md' in registry['entries']['art_001']['past_rel_paths']
        assert validate_catalog_identities(str(base)) is True


def test_draft_and_delete_never_reuses_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        books_dir = base / 'content' / 'books'
        (base / 'content' / 'articles').mkdir(parents=True, exist_ok=True)
        books_dir.mkdir(parents=True, exist_ok=True)

        b1 = books_dir / 'livro-1.md'
        b2 = books_dir / 'livro-2.md'
        b1.write_text('---\ntitle: "Livro Um"\nauthor: "A"\nlicense: "PD"\n---\nCorpo livro um.', encoding='utf-8')
        b2.write_text('---\ntitle: "Livro Dois"\nauthor: "B"\nlicense: "PD"\n---\nCorpo livro dois.', encoding='utf-8')

        update_index(str(base))

        # Marca livro-2 como rascunho e cria livro-3 inédito
        b2.write_text('---\ntitle: "Livro Dois"\nauthor: "B"\nlicense: "PD"\ndraft: true\n---\nCorpo livro dois.', encoding='utf-8')
        b3 = books_dir / 'livro-3.md'
        b3.write_text('---\ntitle: "Livro Três"\nauthor: "C"\nlicense: "PD"\n---\nCorpo livro três.', encoding='utf-8')
        update_index(str(base))

        books_v2 = {b['title']: b['id'] for b in json.loads((base / 'index-books.json').read_text(encoding='utf-8'))['books']}
        assert books_v2['Livro Um'] == 'book_001'
        assert 'Livro Dois' not in books_v2
        assert books_v2['Livro Três'] == 'book_003'  # Jamais reutiliza book_002!

        # Exclui livro-3 (maior ID) e cria livro-4 -> deve avançar para book_004
        b3.unlink()
        b4 = books_dir / 'livro-4.md'
        b4.write_text('---\ntitle: "Livro Quatro"\nauthor: "D"\nlicense: "PD"\n---\nCorpo livro quatro.', encoding='utf-8')
        update_index(str(base))

        books_v3 = {b['title']: b['id'] for b in json.loads((base / 'index-books.json').read_text(encoding='utf-8'))['books']}
        assert books_v3['Livro Quatro'] == 'book_004'

        # Reativa livro-2 -> deve recuperar book_002 exato
        b2.write_text('---\ntitle: "Livro Dois"\nauthor: "B"\nlicense: "PD"\ndraft: false\n---\nCorpo livro dois.', encoding='utf-8')
        update_index(str(base))
        books_v4 = {b['title']: b['id'] for b in json.loads((base / 'index-books.json').read_text(encoding='utf-8'))['books']}
        assert books_v4['Livro Dois'] == 'book_002'

        registry = json.loads((base / REGISTRY_RELATIVE_PATH).read_text(encoding='utf-8'))
        assert registry['sequences']['book'] == 4
        assert registry['entries']['book_003']['status'] == 'retired'
        assert validate_catalog_identities(str(base)) is True


def test_sqlite_validator_rejects_id_hijack_and_deletion():
    previous = {
        'schema_version': 1,
        'sequences': {'art': 0, 'book': 1},
        'entries': {
            'book_001': {
                'id': 'book_001',
                'kind': 'book',
                'status': 'active',
                'current_rel_path': 'platao/fedon.md',
                'past_rel_paths': [],
                'canonical_title': 'Fédon',
                'canonical_author': 'Platão',
                'doi': None,
                'last_body_sha256': 'hash-fedon',
            }
        },
    }
    hijacked = {
        'schema_version': 1,
        'sequences': {'art': 0, 'book': 1},
        'entries': {
            'book_001': {
                'id': 'book_001',
                'kind': 'book',
                'status': 'active',
                'current_rel_path': 'pessoa/mensagem.md',
                'past_rel_paths': [],
                'canonical_title': 'Mensagem',
                'canonical_author': 'Fernando Pessoa',
                'doi': None,
                'last_body_sha256': 'hash-mensagem',
            }
        },
    }

    import pytest
    with pytest.raises(IdentityViolationError):
        validate_registry_snapshot_with_sqlite(previous, hijacked)

    with pytest.raises(IdentityViolationError):
        validate_registry_snapshot_with_sqlite(previous, {'schema_version': 1, 'sequences': {'art': 0, 'book': 1}, 'entries': {}})


