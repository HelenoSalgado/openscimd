import pytest
from pathlib import Path
from scripts.categories import load_allowed_categories, normalize_categories, validate_categories
from scripts.validator import validate_articles, validate_books, validate_all
from scripts.utils import parse_markdown_file, get_files_recursively

BASE_DIR = Path(__file__).resolve().parent.parent


def test_load_allowed_categories():
    cats = load_allowed_categories()
    assert isinstance(cats, list)
    assert len(cats) >= 20
    assert "Computação" in cats
    assert "Política" in cats
    assert "Filosofia" in cats
    assert "História" in cats
    assert "Teologia" in cats
    assert cats == sorted(cats)


def test_normalize_categories():
    raw = ["História", "Filosofia", "História ", "Filosofia"]
    normalized = normalize_categories(raw)
    assert normalized == ["Filosofia", "História"]
    assert normalize_categories([]) == []


def test_validate_categories_valid():
    assert validate_categories(["Filosofia"]) == []
    assert validate_categories(["Filosofia", "História", "Teologia"]) == []


def test_validate_categories_none_or_empty():
    err_none = validate_categories(None)
    assert len(err_none) == 1
    assert "ausente" in err_none[0]

    err_empty = validate_categories([])
    assert len(err_empty) == 1
    assert "vazia" in err_empty[0]

    err_str = validate_categories("Filosofia")
    assert len(err_str) == 1
    assert "deve ser uma lista" in err_str[0]


def test_validate_categories_invalid_and_composite():
    errors = validate_categories(["Filosofia Antiga", "História do Direito"])
    assert len(errors) == 2
    assert "Filosofia Antiga" in errors[0]
    assert "História do Direito" in errors[1]


def test_validate_categories_unsorted():
    errors = validate_categories(["História", "Filosofia"])
    assert len(errors) == 1
    assert "não está ordenada alfabeticamente" in errors[0]


def test_validate_categories_duplicates():
    errors = validate_categories(["Filosofia", "Filosofia"])
    assert any("elementos duplicados" in e for e in errors)


def test_validate_categories_invalid_elements():
    errors = validate_categories(["Filosofia", "", 123])
    assert any("Elemento inválido" in e for e in errors)


def test_all_repository_articles_categories_integrity():
    """Garante que 100% dos artigos do repositório possuem categorias válidas e ordenadas."""
    articles_dir = BASE_DIR / "content" / "articles"
    files = get_files_recursively(articles_dir)
    assert len(files) > 0

    for file_path in files:
        parsed = parse_markdown_file(file_path)
        meta = parsed["metadata"]
        cats = meta.get("categories")
        errors = validate_categories(cats)
        assert errors == [], f"Erro no artigo {file_path}: {errors}"


def test_all_repository_books_categories_integrity():
    """Garante que 100% dos e-books do repositório possuem categorias válidas e ordenadas."""
    books_dir = BASE_DIR / "content" / "books"
    files = get_files_recursively(books_dir)
    assert len(files) > 0

    for file_path in files:
        parsed = parse_markdown_file(file_path)
        meta = parsed["metadata"]
        cats = meta.get("categories")
        errors = validate_categories(cats)
        assert errors == [], f"Erro no livro {file_path}: {errors}"


def test_validators_full_execution():
    """Garante que as funções validate_articles, validate_books e validate_all passam sem erros."""
    assert validate_articles(str(BASE_DIR)) is True
    assert validate_books(str(BASE_DIR)) is True
    assert validate_all(str(BASE_DIR)) is True
