import shutil
import zipfile
from datetime import date
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from main import app
from scripts.kindle_validator import validate_kindle_epub
from scripts.md2epub import (
    batch_convert_content,
    convert_md_to_epub,
    extract_frontmatter,
    find_cover_image,
    format_editorial_date,
    generate_colophon_markdown,
    generate_frontmatter_editorial_blocks,
    generate_institutional_page,
    normalize_github_alerts,
    normalize_headings_and_preamble,
    resolve_author_name,
    resolve_authors_list,
    resolve_epub_output_path,
    separate_consecutive_verses,
    strip_empty_footnote_sections,
)

runner = CliRunner()


def test_extract_frontmatter():
    sample = """---
title: "Título de Teste"
author: "Autor de Teste"
language: "pt-BR"
---

# Capítulo 1

Texto do capítulo.
"""
    meta, body = extract_frontmatter(sample)
    assert meta["title"] == "Título de Teste"
    assert meta["author"] == "Autor de Teste"
    assert meta["language"] == "pt-BR"
    assert "# Capítulo 1" in body


def test_extract_frontmatter_empty():
    sample = "# Sem frontmatter\n\nApenas texto."
    meta, body = extract_frontmatter(sample)
    assert meta == {}
    assert body == sample


def test_resolve_authors_from_author_and_authors_list():
    assert resolve_author_name({"author": "Platão"}) == "Platão"
    assert resolve_authors_list({"authors": [{"name": "Santo Inácio de Antioquia"}]}) == [
        "Santo Inácio de Antioquia"
    ]
    multi = {"authors": [{"name": "Jorge Ramos do Ó"}, {"name": "Ana Luísa Paz"}]}
    assert resolve_author_name(multi) == "Jorge Ramos do Ó, Ana Luísa Paz"
    assert resolve_author_name({}, default="OpenSciMD") == "OpenSciMD"


def test_generate_colophon():
    meta = {
        "title": "A República",
        "authors": [{"name": "Platão"}],
        "translator": "Heleno Salgado",
        "publisher": "OpenSciMD",
        "license": "Domínio Público",
    }
    colophon = generate_colophon_markdown(meta)
    assert "{.unnumbered .unlisted}" in colophon
    assert "OpenSciMD" in colophon
    assert "Platão" in colophon
    assert "Heleno Salgado" in colophon
    assert "colophon-box" in colophon


def test_generate_frontmatter_editorial_blocks_no_double_dots():
    meta = {
        "title": "Apologia de Sócrates",
        "author": "Platão",
        "translator": "Heleno Salgado",
        "publisher": "OpenSciMD",
        "license": "Domínio Público.",
        "date": "399 a.C.",
        "categories": ["Filosofia"],
    }
    blocks = generate_frontmatter_editorial_blocks(meta)
    assert "editorial-titlepage" in blocks
    assert "catalographic-box" in blocks
    assert "Composição canônica: 399 a.C." in blocks
    assert "399 a.C.." not in blocks
    assert "Domínio Público.." not in blocks
    assert "Traduzido por Heleno Salgado" in blocks

    modern_meta = {
        "title": "Artigo Moderno",
        "author": "Autor",
        "date": "2026-08-06",
    }
    modern_blocks = generate_frontmatter_editorial_blocks(modern_meta)
    assert "6 de agosto de 2026" in modern_blocks
    assert "2026-08-06" not in modern_blocks


def test_format_editorial_date():
    assert format_editorial_date("2026-08-06") == "6 de agosto de 2026"
    assert format_editorial_date("20-11-2025") == "20 de novembro de 2025"
    assert format_editorial_date("2026-08") == "agosto de 2026"
    assert format_editorial_date(date(2026, 8, 6)) == "6 de agosto de 2026"
    assert format_editorial_date("386 d.C") == "386 d.C."
    assert format_editorial_date("107 d. C.") == "107 d.C."
    assert format_editorial_date("c. 385 a.C.") == "c. 385 a.C."
    assert format_editorial_date("1576") == "1576"


def test_generate_institutional_page():
    page_md = generate_institutional_page()
    assert "institutional-card" in page_md
    assert "OpenSciMD &amp; Leia-me" in page_md
    assert "leiame.app" in page_md
    assert "Língua Portuguesa" in page_md
    assert "Portuguêsa" not in page_md
    assert "CC BY-NC-ND 4.0" in page_md
    assert "Salgado, H. (2026). OpenSciMD: Open-Access Scientific Articles in Markdown (Version 1.1.0) [Data set]." in page_md
    assert "https://github.com/HelenoSalgado/openscimd" in page_md


def test_epub_css_play_books_and_kindle_compliance():
    css_path = Path("scripts/templates/epub.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")

    # Google Play Books: sem @namespace (causava erro unknown @ rule at line 1 column 1)
    assert "@namespace" not in content
    assert "text-justify" not in content
    assert "word-break: break-all" not in content

    # h2 não pode forçar quebra de página e deve aproximar subtítulo imediato no Pandoc (<section>)
    assert "page-break-before: auto;" in content
    assert "break-before: auto;" in content
    assert "h2 {" in content
    assert "h1 + section > h2" in content
    assert "h2 + section > h3" in content

    # .footnote-ref deve ter vertical-align: super explícito e cor dourada (#8B6B23)
    assert ".footnote-ref {" in content
    assert "vertical-align: super;" in content
    assert "a, a:visited {" in content
    assert "color: #8B6B23;" in content

    # Estilização para figuras, imagens, tabelas e citation-box
    assert "figure {" in content
    assert "figcaption" in content
    assert "table {" in content
    assert ".citation-box" in content
    assert "color: #2D3748;" in content
    assert "@media (prefers-color-scheme: dark)" in content

    # Sem propriedades proprietárias inválidas ou pseudo-classes não suportadas
    assert "-webkit-text-size-adjust" not in content
    assert "-webkit-hyphens" not in content
    assert "adobe-hyphenate" not in content
    assert ":has(" not in content


def test_strip_empty_footnote_sections():
    raw = """## Capítulo Final

Texto conclusivo[^ne1][^1].

---

### Notas Editoriais

[^ne1]: Nota editorial importante.

### Notas do Autor

[^1]: Nota do autor.

---

### Referências

[1]: Obra citada real que deve permanecer.

---
"""
    cleaned = strip_empty_footnote_sections(raw)
    assert "### Notas Editoriais" not in cleaned
    assert "### Notas do Autor" not in cleaned
    assert "[^ne1]: Nota editorial importante." in cleaned
    assert "[^1]: Nota do autor." in cleaned
    assert "### Referências" in cleaned
    assert "[1]: Obra citada real que deve permanecer." in cleaned
    assert not cleaned.strip().endswith("---")


def test_normalize_alerts_and_verses():
    alert_md = "> [!NOTE]\n> Texto da nota editorial."
    norm_alert = normalize_github_alerts(alert_md)
    assert "[!NOTE]" not in norm_alert
    assert "> **Nota:** Texto da nota editorial." in norm_alert

    verses_md = "## Capítulo 1\n\n¹ No princípio.\n² E a terra era sem forma."
    norm_verses = separate_consecutive_verses(verses_md)
    assert "¹ No princípio.\n\n² E a terra era sem forma." in norm_verses


def test_normalize_headings_and_preamble():
    # 1. Título H1 redundante antes de H2 (ex: Poética)
    body_dup = "# Poética\n\n## I\n\nTexto."
    norm_1, shift_1, pref_1 = normalize_headings_and_preamble(body_dup, "Poética")
    assert "# Poética" not in norm_1
    assert shift_1 is True
    assert pref_1 == "##"

    # 2. Salto H1 -> H3 sem H2 (ex: Solilóquios)
    body_gap = "# LIVRO PRIMEIRO\n\n### 1. 1.\n\nDiálogo."
    norm_2, shift_2, pref_2 = normalize_headings_and_preamble(body_gap, "Solilóquios")
    assert "## 1. 1." in norm_2
    assert "### 1. 1." not in norm_2
    assert shift_2 is False
    assert pref_2 == "#"

    # 3. Artigo sem cabeçalhos
    body_flat = "Parágrafo único de artigo clássico."
    norm_3, shift_3, pref_3 = normalize_headings_and_preamble(body_flat, "Estudo Clássico")
    assert norm_3.startswith("## Estudo Clássico")
    assert shift_3 is True


def test_find_cover_image_not_found(tmp_path):
    dummy_book = tmp_path / "dummy-book.md"
    dummy_book.write_text("# Teste", encoding="utf-8")
    assert find_cover_image(dummy_book, tmp_path) is None


def test_find_cover_image_found_and_webp_fallback(tmp_path):
    covers_dir = tmp_path / "assets" / "covers" / "originals"
    covers_dir.mkdir(parents=True)
    cover_file = covers_dir / "obra-antiga.png"
    cover_file.write_bytes(b"dummy image data")

    dummy_book = tmp_path / "content" / "books" / "obra-antiga.md"
    dummy_book.parent.mkdir(parents=True)
    dummy_book.write_text("# Teste", encoding="utf-8")
    assert find_cover_image(dummy_book, tmp_path) == cover_file

    webp_cover = covers_dir / "artigo-webp.webp"
    Image.new("RGB", (40, 60), color=(20, 30, 50)).save(webp_cover, format="WEBP")
    dummy_art = tmp_path / "content" / "articles" / "artigo-webp.md"
    dummy_art.parent.mkdir(parents=True)
    dummy_art.write_text("# Teste", encoding="utf-8")
    assert find_cover_image(dummy_art, tmp_path) == webp_cover


@pytest.mark.skipif(not shutil.which("pandoc"), reason="O executável 'pandoc' não está instalado no sistema operacional.")
def test_convert_md_to_epub_with_webp_assets_and_authors_list(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")

    # Criar capa WebP e figura WebP referenciada como /assets/desktop/fig1.webp
    cover_dir = tmp_path / "assets" / "covers" / "originals"
    cover_dir.mkdir(parents=True)
    Image.new("RGB", (300, 450), color=(30, 40, 70)).save(cover_dir / "livro-teste.webp", format="WEBP")

    fig_dir = tmp_path / "assets" / "desktop"
    fig_dir.mkdir(parents=True)
    Image.new("RGB", (200, 120), color=(120, 90, 40)).save(fig_dir / "fig1.webp", format="WEBP")

    book_file = tmp_path / "livro-teste.md"
    book_file.write_text(
        """---
title: "Livro de Exemplo"
authors:
  - name: "Pensador Notável"
translator: "Heleno Salgado"
language: "pt-BR"
date: "399 a.C."
summary: "Um resumo conciso sobre o exemplar."
---

![Ilustração Histórica](/assets/desktop/fig1.webp)

## Capítulo Primeiro[^ne1]

Este é o início do texto editorial.

### Subseção Dialética

Argumentação lógica e coerente.

---

### Notas Editoriais

[^ne1]: Nota editorial convertida para rodapé sem deixar seção vazia.
""",
        encoding="utf-8",
    )

    out_epub = tmp_path / "output.epub"
    res_path = convert_md_to_epub(
        input_md_path=book_file,
        output_epub_path=out_epub,
        base_dir=tmp_path,
        add_colophon=True,
    )

    assert res_path.exists()
    val = validate_kindle_epub(res_path)
    assert val.is_valid is True, f"Erros de validação: {val.errors}"
    assert val.warnings == [], f"Avisos inesperados: {val.warnings}"

    with zipfile.ZipFile(res_path, "r") as z:
        namelist = z.namelist()
        assert not any(n.endswith(".webp") for n in namelist)
        assert any(n.endswith(".png") for n in namelist)

        opf_name = next(name for name in namelist if name.endswith(".opf"))
        opf_content = z.read(opf_name).decode("utf-8")
        assert "Livro de Exemplo" in opf_content
        assert "Pensador Notável" in opf_content
        assert 'title="Capa"' in opf_content

        nav_name = next(name for name in namelist if name.endswith("nav.xhtml"))
        nav_content = z.read(nav_name).decode("utf-8")
        assert "Notas Editoriais" not in nav_content
        assert '<h1 id="toc-title">Sumário</h1>' in nav_content
        assert "<title>Sumário</title>" in nav_content
        assert "Livro de Exemplo" not in nav_content
        assert ">Capa</a>" in nav_content
        assert ">Sumário</a>" in nav_content

        for xhtml_name in [n for n in namelist if n.endswith(".xhtml")]:
            xhtml_txt = z.read(xhtml_name).decode("utf-8")
            assert "<style>" not in xhtml_txt
            assert ".xhtml</title>" not in xhtml_txt
            if 'class="footnote-ref"' in xhtml_txt:
                assert "<sup>1</sup></a>" in xhtml_txt


def test_convert_md_to_epub_missing_file():
    with pytest.raises(FileNotFoundError):
        convert_md_to_epub("arquivo_totalmente_inexistente.md")


@pytest.mark.skipif(not shutil.which("pandoc"), reason="O executável 'pandoc' não está instalado no sistema operacional.")
def test_cli_build_epub(tmp_path):
    book_file = tmp_path / "filosofia.md"
    book_file.write_text(
        """---
title: "Filosofia Primeira"
author: "Aristóteles"
language: "pt-BR"
---

## Do Ser

O ser se diz de muitos modos.
""",
        encoding="utf-8",
    )
    out_epub = tmp_path / "filosofia.epub"

    result = runner.invoke(app, ["build-epub", str(book_file), "--output", str(out_epub)])
    assert result.exit_code == 0
    assert "EPUB gerado com sucesso!" in result.stdout
    assert out_epub.exists()


def test_resolve_epub_output_path(tmp_path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    books_file = project_root / "content" / "books" / "platao" / "dialogo.md"
    books_file.parent.mkdir(parents=True)
    books_file.write_text("# Dialogo")

    resolved = resolve_epub_output_path(books_file, project_root, structured=True)
    expected = project_root / "dist" / "content" / "books" / "platao" / "dialogo.epub"
    assert resolved == expected

    resolved_flat = resolve_epub_output_path(books_file, project_root, structured=False)
    expected_flat = project_root / "dist" / "dialogo.epub"
    assert resolved_flat == expected_flat

    custom_target = tmp_path / "custom" / "livro.epub"
    resolved_custom = resolve_epub_output_path(books_file, project_root, output_epub_path=custom_target)
    assert resolved_custom == custom_target


@pytest.mark.skipif(not shutil.which("pandoc"), reason="O executável 'pandoc' não está instalado no sistema operacional.")
def test_batch_convert_content(tmp_path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    book = project_root / "content" / "books" / "autor1" / "obra.md"
    book.parent.mkdir(parents=True)
    book.write_text("---\ntitle: 'Obra 1'\nauthor: 'Autor 1'\n---\n\n## Cap 1\n\nConteúdo.")

    art = project_root / "content" / "articles" / "rev1" / "artigo.md"
    art.parent.mkdir(parents=True)
    art.write_text("---\ntitle: 'Artigo 1'\nauthors:\n  - name: 'Autor 2'\n---\n\n## Introdução\n\nTexto.")

    res = batch_convert_content(base_dir=project_root)
    assert res["total"] == 2
    assert len(res["succeeded"]) == 2
    assert len(res["failed"]) == 0

    expected_book_epub = project_root / "dist" / "content" / "books" / "autor1" / "obra.epub"
    expected_art_epub = project_root / "dist" / "content" / "articles" / "rev1" / "artigo.epub"
    assert expected_book_epub.exists()
    assert expected_art_epub.exists()


@pytest.mark.skipif(not shutil.which("pandoc"), reason="O executável 'pandoc' não está instalado no sistema operacional.")
def test_cli_build_epub_all_and_validate_kindle(tmp_path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    book = project_root / "content" / "books" / "platao" / "fedro.md"
    book.parent.mkdir(parents=True)
    book.write_text("---\ntitle: 'Fedro'\nauthor: 'Platão'\n---\n\n## Discurso\n\nSobre a retórica.")

    res_err = runner.invoke(app, ["build-epub"])
    assert res_err.exit_code == 1
    assert "Forneça o caminho do arquivo Markdown ou utilize a flag '--all'" in res_err.stdout

    try:
        res_build = runner.invoke(app, ["build-epub", str(book)])
        assert res_build.exit_code == 0
        generated_epub = Path("dist/content/books/platao/fedro.epub")
        assert generated_epub.exists()

        res_val = runner.invoke(app, ["validate-kindle", str(generated_epub)])
        assert res_val.exit_code == 0
        assert "APROVADO" in res_val.stdout
    finally:
        generated_epub = Path("dist/content/books/platao/fedro.epub")
        if generated_epub.exists():
            generated_epub.unlink()
        if generated_epub.parent.exists() and not any(generated_epub.parent.iterdir()):
            generated_epub.parent.rmdir()
