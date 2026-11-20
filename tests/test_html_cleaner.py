"""Testes unitários para o extrator semântico LegacyHtmlCleaner."""

from __future__ import annotations

from pathlib import Path

from scripts.html_cleaner import LegacyHtmlCleaner


def test_decode_html_bytes() -> None:
    raw_iso = "Hugo de São Vítor: A Palavra de Deus".encode("iso-8859-1")
    decoded = LegacyHtmlCleaner.decode_html_bytes(raw_iso)
    assert decoded == "Hugo de São Vítor: A Palavra de Deus"


def test_convert_tables_to_blockquotes() -> None:
    html = """
    <html><body>
    <table width="100%">
      <tr><td align="center"><font size="3"><b><i>"Uma só vez falou Deus".</i></b></font></td></tr>
    </table>
    <table width="100%">
      <tr><td width="50%"></td><td width="50%"><tt>Salmo 61, 12</tt></td></tr>
    </table>
    </body></html>
    """
    _, md = LegacyHtmlCleaner.clean_html_document(html)
    assert "> “Uma só vez falou Deus.”" in md
    assert "— Salmo 61, 12" in md


def test_sanitize_spurious_h4() -> None:
    html = """
    <html><body>
    <h3>1. Introdução</h3>
    <h4>Este é um parágrafo longo explicativo sobre o amor divino que foi erroneamente formatado como tag de cabeçalho no HTML legado da página web.</h4>
    <p>Continuação normal do parágrafo explicativo.</p>
    </body></html>
    """
    _, md = LegacyHtmlCleaner.clean_html_document(html)
    assert "### 1. Introdução" in md
    assert "#### Este é um parágrafo longo" not in md
    assert "Este é um parágrafo longo explicativo sobre o amor divino" in md


def test_remove_navigation_residuals() -> None:
    html = """
    <html><body>
    <p>Texto do tratado vitorino.</p>
    <hr>
    <h5>Índice da Página</h5>
    <a href="sum-hugo.htm">Sumário</a>
    </body></html>
    """
    _, md = LegacyHtmlCleaner.clean_html_document(html)
    assert "Texto do tratado vitorino." in md
    assert "Índice da Página" not in md
    assert "sum-hugo.htm" not in md


def test_convert_file_end_to_end(tmp_path: Path) -> None:
    sample_html = tmp_path / "sample.htm"
    sample_html.write_text(
        "<html><head><title>Tratado da Palavra</title></head><body>"
        "<h2>Hugo de São Vítor</h2>"
        "<h3>Capítulo 1</h3><p>O Verbo se fez carne.</p>"
        "</body></html>",
        encoding="utf-8",
    )
    output_md = tmp_path / "sample.md"
    result = LegacyHtmlCleaner.convert_file(sample_html, output_md, part_title="A Palavra de Deus")

    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert 'title: "A Palavra de Deus"' in content
    assert 'author: "Hugo de São Vítor"' in content
    assert "### Capítulo 1" in content
    assert "O Verbo se fez carne." in content


def test_preserves_inline_emphasis_and_generic_author(tmp_path: Path) -> None:
    html = (
        '<html><head><title>Diálogo</title><meta name="author" content="Platão"></head>'
        "<body><p>Conhece-te a <i>ti mesmo</i> como <b>princípio</b>.</p></body></html>"
    )
    meta, md = LegacyHtmlCleaner.clean_html_document(html)
    assert meta["author"] == "Platão"
    assert "Conhece-te a *ti mesmo* como **princípio**." in md

    meta_anon, _ = LegacyHtmlCleaner.clean_html_document("<html><body><p>Sem autor.</p></body></html>")
    assert meta_anon["author"] == "Desconhecido"

    meta_override, _ = LegacyHtmlCleaner.clean_html_document(
        "<html><body><p>Texto.</p></body></html>",
        author="Agostinho",
    )
    assert meta_override["author"] == "Agostinho"
