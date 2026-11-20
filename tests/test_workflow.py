"""Testes unitários e de integração para o fluxo start-review e promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.workflow import WorkflowError, promote_review, start_review


def _valid_article_text() -> str:
    return (
        "---\n"
        'title: "Artigo Válido em Revisão"\n'
        "authors:\n"
        '  - name: "Autor Teste"\n'
        'summary: "Resumo integral do artigo."\n'
        'date: "2026-06-20"\n'
        'license: "CC BY 4.0"\n'
        'pages: "1–10"\n'
        'language: "pt-BR"\n'
        "categories:\n"
        "  - Filosofia\n"
        "---\n\n"
        "## Introdução\n\n"
        "Texto revisado conforme padrão editorial com aspas “curvas” e nota[^1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Referência original.\n"
    )


def test_start_review_from_draft_preserves_draft_and_creates_audit(tmp_path: Path) -> None:
    draft_dir = tmp_path / "data" / "draft"
    draft_dir.mkdir(parents=True)
    draft_file = draft_dir / "artigo-bruto.md"
    draft_content = "---\ntitle: Rascunho\n---\n\n" + "\n".join(f"Linha {i}" for i in range(1, 251))
    draft_file.write_text(draft_content, encoding="utf-8")

    res = start_review(
        draft_file,
        base_dir=tmp_path,
        doc_type="articles",
        dest_rel="revista-teste/vol-1/artigo-final.md",
    )

    assert draft_file.exists()
    assert draft_file.read_text(encoding="utf-8") == draft_content
    assert res.review_path == (tmp_path / "data" / "review" / "articles" / "revista-teste" / "vol-1" / "artigo-final.md").resolve()
    assert res.review_path.exists()
    assert res.audit_path is not None and res.audit_path.exists()
    assert res.block_count == 2
    audit_txt = res.audit_path.read_text(encoding="utf-8")
    assert "Bloco 1" in audit_txt
    assert "Bloco 2" in audit_txt


def test_start_review_from_published_content_mirrors_path(tmp_path: Path) -> None:
    book_dir = tmp_path / "content" / "books" / "platao"
    book_dir.mkdir(parents=True)
    book_file = book_dir / "fedon.md"
    book_file.write_text("---\ntitle: Fédon\n---\n\n## Capítulo I\n\nTexto.", encoding="utf-8")

    res = start_review(book_file, base_dir=tmp_path)

    assert book_file.exists()
    expected = (tmp_path / "data" / "review" / "books" / "platao" / "fedon.md").resolve()
    assert res.review_path == expected
    assert expected.exists()
    assert res.doc_type == "books"


def test_promote_review_blocks_invalid_file_without_touching_content(tmp_path: Path) -> None:
    review_dir = tmp_path / "data" / "review" / "articles" / "revista" / "vol-1"
    review_dir.mkdir(parents=True)
    bad_file = review_dir / "artigo-ruim.md"
    bad_file.write_text(
        '---\ntitle: "Artigo"\nauthor: "Autor"\nsummary: "Res"\ndate: "2026-06-20"\n'
        'license: "CC BY 4.0"\npages: "1–5"\nlanguage: "pt-BR"\ncategories: ["Filosofia"]\n---\n\n'
        '# H1 Proibido\n\nTexto com "aspas retas".\n',
        encoding="utf-8",
    )

    with pytest.raises(WorkflowError, match="Promoção bloqueada"):
        promote_review(bad_file, base_dir=tmp_path)

    assert bad_file.exists()
    assert not (tmp_path / "content" / "articles" / "revista" / "vol-1" / "artigo-ruim.md").exists()


def test_promote_review_moves_to_content_and_cleans_review_and_audit(tmp_path: Path) -> None:
    (tmp_path / "content" / "articles").mkdir(parents=True)
    (tmp_path / "content" / "books").mkdir(parents=True)
    review_dir = tmp_path / "data" / "review" / "articles" / "revista" / "vol-2"
    review_dir.mkdir(parents=True)

    rev_file = review_dir / "artigo-bom.md"
    rev_file.write_text(_valid_article_text() + "\n", encoding="utf-8")
    # Garante volume: 2 para bater com vol-2
    rev_file.write_text(
        rev_file.read_text(encoding="utf-8").replace('pages: "1–10"', 'volume: 2\npages: "1–10"'),
        encoding="utf-8",
    )
    audit_file = rev_file.with_suffix(".audit.md")
    audit_file.write_text("# Audit", encoding="utf-8")

    dry = promote_review(rev_file, base_dir=tmp_path, dry_run=True)
    assert dry.dry_run is True
    assert rev_file.exists()

    res = promote_review(rev_file, base_dir=tmp_path, run_index=True)
    expected_dest = (tmp_path / "content" / "articles" / "revista" / "vol-2" / "artigo-bom.md").resolve()

    assert res.dry_run is False
    assert res.indexed is True
    assert res.content_path == expected_dest
    assert expected_dest.exists()
    assert not rev_file.exists()
    assert not audit_file.exists()
    assert (tmp_path / "index-articles.json").exists()
