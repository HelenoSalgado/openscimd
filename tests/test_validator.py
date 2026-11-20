"""Testes unitários para validação de categorias, metadados YAML e arquivo individual."""

from __future__ import annotations

from pathlib import Path

from scripts.categories import (
    derive_udc_from_categories,
    load_allowed_categories,
    normalize_categories,
    validate_categories,
)
from scripts.validator import (
    validate_all,
    validate_articles,
    validate_books,
    validate_single_file,
)


def test_derive_udc_from_categories() -> None:
    assert derive_udc_from_categories(None) is None
    assert derive_udc_from_categories([]) is None
    assert derive_udc_from_categories(["Filosofia"]) == "1"
    assert derive_udc_from_categories(["Teologia"]) == "2"
    assert derive_udc_from_categories(["Poesia"]) == "82-1"
    assert derive_udc_from_categories(["Filosofia", "História"]) == "1:94"
    assert derive_udc_from_categories(["Computação"]) == "004"
    assert derive_udc_from_categories(["CategoriaInexistente"]) is None


def test_load_allowed_categories() -> None:
    cats = load_allowed_categories()
    assert isinstance(cats, list)
    assert len(cats) >= 23
    assert "Computação" in cats
    assert "Poesia" in cats
    assert "Política" in cats
    assert "Filosofia" in cats
    assert "História" in cats
    assert "Teologia" in cats
    assert cats == sorted(cats)


def test_normalize_categories() -> None:
    raw = ["História", "Filosofia", "História ", "Filosofia"]
    normalized = normalize_categories(raw)
    assert normalized == ["Filosofia", "História"]
    assert normalize_categories([]) == []


def test_validate_categories_valid() -> None:
    assert validate_categories(["Filosofia"]) == []
    assert validate_categories(["Filosofia", "História", "Teologia"]) == []


def test_validate_categories_none_or_empty() -> None:
    err_none = validate_categories(None)
    assert len(err_none) == 1
    assert "ausente" in err_none[0]

    err_empty = validate_categories([])
    assert len(err_empty) == 1
    assert "vazia" in err_empty[0]

    err_str = validate_categories("Filosofia")
    assert len(err_str) == 1
    assert "deve ser uma lista" in err_str[0]


def test_validate_categories_invalid_and_composite() -> None:
    errors = validate_categories(["Filosofia Antiga", "História do Direito"])
    assert len(errors) == 2
    assert "Filosofia Antiga" in errors[0]
    assert "História do Direito" in errors[1]


def test_validate_categories_unsorted() -> None:
    errors = validate_categories(["História", "Filosofia"])
    assert len(errors) == 1
    assert "não está ordenada alfabeticamente" in errors[0]


def test_validate_categories_duplicates() -> None:
    errors = validate_categories(["Filosofia", "Filosofia"])
    assert any("elementos duplicados" in e for e in errors)


def test_validate_categories_invalid_elements() -> None:
    errors = validate_categories(["Filosofia", "", 123])
    assert any("Elemento inválido" in e for e in errors)


def test_all_repository_articles_categories_integrity() -> None:
    """Garante que 100% dos artigos do repositório possuem categorias válidas e ordenadas."""
    from scripts.utils import get_files_recursively, parse_markdown_file

    base_dir = Path(__file__).resolve().parent.parent
    articles_dir = base_dir / "content" / "articles"
    files = get_files_recursively(articles_dir)
    assert len(files) > 0

    for file_path in files:
        parsed = parse_markdown_file(file_path)
        meta = parsed["metadata"]
        cats = meta.get("categories")
        errors = validate_categories(cats)
        assert errors == [], f"Erro no artigo {file_path}: {errors}"


def test_all_repository_books_categories_integrity() -> None:
    """Garante que 100% dos e-books do repositório possuem categorias válidas e ordenadas."""
    from scripts.utils import get_files_recursively, parse_markdown_file

    base_dir = Path(__file__).resolve().parent.parent
    books_dir = base_dir / "content" / "books"
    files = get_files_recursively(books_dir)
    assert len(files) > 0

    for file_path in files:
        parsed = parse_markdown_file(file_path)
        meta = parsed["metadata"]
        cats = meta.get("categories")
        errors = validate_categories(cats)
        assert errors == [], f"Erro no livro {file_path}: {errors}"


def test_validators_full_execution() -> None:
    """Garante que as funções validate_articles, validate_books e validate_all passam sem erros."""
    base_dir = Path(__file__).resolve().parent.parent
    assert validate_articles(str(base_dir)) is True
    assert validate_books(str(base_dir)) is True
    assert validate_all(str(base_dir)) is True


def test_validate_articles_volume_consistency(tmp_path: Path) -> None:
    """Garante que a divergência entre pasta vol-X e volume no frontmatter é barrada."""
    art_dir = tmp_path / "content" / "articles" / "test-journal" / "vol-2"
    art_dir.mkdir(parents=True)

    file_path = art_dir / "artigo.md"
    file_path.write_text(
        "---\ntitle: 'Artigo Teste'\nauthor: 'Autor'\nsummary: 'Resumo'\n"
        "date: '2020-01-01'\nlicense: 'CC BY 4.0'\npages: '1–10'\n"
        "categories: ['Filosofia']\nvolume: 1\n---\nCorpo",
        encoding="utf-8",
    )
    assert validate_articles(str(tmp_path)) is False

    file_path.write_text(
        "---\ntitle: 'Artigo Teste'\nauthor: 'Autor'\nsummary: 'Resumo'\n"
        "date: '2020-01-01'\nlicense: 'CC BY 4.0'\npages: '1–10'\n"
        "categories: ['Filosofia']\nvolume: 2\n---\nCorpo",
        encoding="utf-8",
    )
    assert validate_articles(str(tmp_path)) is True


def test_validate_single_file_accepts_abnt_date_and_enforces_language_and_editorial(tmp_path: Path) -> None:
    review_dir = tmp_path / "data" / "review" / "articles" / "revista" / "vol-1"
    review_dir.mkdir(parents=True)

    valid_file = review_dir / "bom.md"
    valid_file.write_text(
        "---\n"
        'title: "Estudo sobre Lógica"\n'
        "authors:\n"
        '  - name: "Autor Teste"\n'
        'summary: "Resumo integral"\n'
        'date: "20 nov. 2025"\n'
        'license: "CC BY 4.0"\n'
        'pages: "1–10"\n'
        "volume: 1\n"
        'language: "pt-BR"\n'
        "categories:\n"
        "  - Filosofia\n"
        "---\n\n"
        "## Introdução\n\n"
        "Texto limpo com nota[^1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Referência.\n",
        encoding="utf-8",
    )
    res_ok = validate_single_file(valid_file, base_dir=tmp_path, check_editorial=True)
    assert res_ok.is_valid()

    bad_file = review_dir / "ruim.md"
    bad_file.write_text(
        "---\n"
        'title: "Sem Título"\n'
        'author: "Desconhecido"\n'
        'summary: "Resumo"\n'
        'date: "2025-11-20"\n'
        'license: "CC BY 4.0"\n'
        'pages: "1–10"\n'
        "volume: 1\n"
        'language: "pt"\n'
        "categories:\n"
        "  - Filosofia\n"
        "---\n\n"
        "# H1 Indevido\n\n"
        'Corpo com "aspas retas".\n',
        encoding="utf-8",
    )
    res_bad = validate_single_file(bad_file, base_dir=tmp_path, check_editorial=True)
    assert not res_bad.is_valid()
    assert any("placeholder" in err for err in res_bad.errors)
    assert any('Campo "language"' in err for err in res_bad.errors)
    ed_codes = {issue.code for issue in res_bad.all_editorial_issues}
    assert {"ED001", "ED005"}.issubset(ed_codes)
