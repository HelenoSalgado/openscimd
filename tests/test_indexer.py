import json
import tempfile
from pathlib import Path
from scripts.indexer import update_articles_index, update_journals_index, update_books_index, update_index
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
