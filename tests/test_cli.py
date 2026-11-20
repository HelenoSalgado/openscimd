"""Testes de integração da CLI Typer (main.py)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import main
from main import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "OpenSciMD CLI para gerenciamento de artigos e livros." in result.stdout
    assert "import-pdf" in result.stdout
    assert "start-review" in result.stdout
    assert "lint" in result.stdout
    assert "promote" in result.stdout


def test_cli_clean_md(tmp_path: Path) -> None:
    pytest.importorskip("salopdoc", reason="salopdoc é dependência opcional do pipeline")
    md_file = tmp_path / "test.md"
    md_file.write_text('# Test Article\n\nSome text with "quotes".\n', encoding="utf-8")

    out_file = tmp_path / "cleaned.md"
    result = runner.invoke(app, ["clean-md", str(md_file), "--output", str(out_file)])
    assert result.exit_code == 0
    assert "Markdown normalizado com sucesso" in result.stdout
    assert out_file.exists()


def test_cli_import_pdf_missing_file() -> None:
    pytest.importorskip("salopdoc", reason="salopdoc é dependência opcional do pipeline")
    result = runner.invoke(app, ["import-pdf", "non_existent_file.pdf"])
    assert result.exit_code != 0
    assert "Erro ao converter PDF" in result.stdout


def test_cli_clean_html(tmp_path: Path) -> None:
    html_file = tmp_path / "test.htm"
    html_file.write_text("<html><body><h3>Título</h3><p>Parágrafo de teste.</p></body></html>", encoding="utf-8")
    out_file = tmp_path / "out.md"
    result = runner.invoke(
        app,
        ["clean-html", str(html_file), str(out_file), "--title", "Título Customizado", "--author", "Autor X"],
    )
    assert result.exit_code == 0
    assert "HTML convertido com sucesso" in result.stdout
    assert out_file.exists()
    assert 'author: "Autor X"' in out_file.read_text(encoding="utf-8")


def test_cli_assemble_book(tmp_path: Path) -> None:
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()
    (parts_dir / "01-cap.md").write_text("---\ntitle: Cap 1\n---\nTexto", encoding="utf-8")
    out_book = tmp_path / "book.md"
    result = runner.invoke(app, ["assemble-book", str(parts_dir), str(out_book), "--title", "Livro Teste"])
    assert result.exit_code == 0
    assert "Volume compilado com sucesso" in result.stdout
    assert out_book.exists()


def test_cli_normalize_refs_canonical(tmp_path: Path) -> None:
    md = tmp_path / "ref.md"
    md.write_text("Veja João 3:16, HB 11:1, 1Coríntios 10:13 e Jo 1:1-14.", encoding="utf-8")
    res = runner.invoke(app, ["normalize-refs", str(md)])
    assert res.exit_code == 0
    content = md.read_text(encoding="utf-8")
    assert "João 3.16" in content
    assert "Hb 11.1" in content
    assert "1 Coríntios 10.13" in content
    assert "Jo 1.1–14" in content

    res_force = runner.invoke(app, ["normalize-refs", str(md), "--force-abbrev"])
    assert res_force.exit_code == 0
    forced = md.read_text(encoding="utf-8")
    assert "Jo 3.16" in forced
    assert "1Co 10.13" in forced


def test_cli_start_review_validate_lint_and_promote(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)

    (tmp_path / "content" / "articles").mkdir(parents=True)
    (tmp_path / "content" / "books").mkdir(parents=True)
    draft_dir = tmp_path / "data" / "draft"
    draft_dir.mkdir(parents=True)

    draft_md = draft_dir / "ensaio.md"
    draft_md.write_text(
        "---\n"
        'title: "Ensaio sobre Lógica"\n'
        "authors:\n"
        '  - name: "Autor Teste"\n'
        'summary: "Resumo integral."\n'
        'date: "2026-06-20"\n'
        'license: "CC BY 4.0"\n'
        'journal: "Revista Teste"\n'
        'DOI: "10.5281/zenodo.123456"\n'
        "volume: 1\n"
        'pages: "1–10"\n'
        'language: "pt-BR"\n'
        "categories:\n"
        "  - Filosofia\n"
        "---\n\n"
        "## Introdução\n\n"
        "Texto válido com nota[^1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Referência.\n",
        encoding="utf-8",
    )

    res_start = runner.invoke(
        app,
        ["start-review", str(draft_md), "--type", "articles", "--dest", "rev/vol-1/ensaio.md"],
    )
    assert res_start.exit_code == 0
    rev_file = tmp_path / "data" / "review" / "articles" / "rev" / "vol-1" / "ensaio.md"
    assert rev_file.exists()

    res_lint = runner.invoke(app, ["lint", str(rev_file), "--strict"])
    assert res_lint.exit_code == 0

    res_val = runner.invoke(app, ["validate", "--file", str(rev_file), "--strict"])
    assert res_val.exit_code == 0

    res_dry = runner.invoke(app, ["promote", str(rev_file), "--dry-run"])
    assert res_dry.exit_code == 0
    assert rev_file.exists()

    res_promote = runner.invoke(app, ["promote", str(rev_file), "--index"])
    assert res_promote.exit_code == 0
    assert not rev_file.exists()
    assert (tmp_path / "content" / "articles" / "rev" / "vol-1" / "ensaio.md").exists()
