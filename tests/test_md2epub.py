import zipfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from main import app
from scripts.md2epub import (
    batch_convert_content,
    convert_md_to_epub,
    extract_frontmatter,
    find_cover_image,
    generate_colophon_markdown,
    generate_frontmatter_editorial_blocks,
    generate_institutional_page,
    resolve_epub_output_path,
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


def test_generate_colophon():
    meta = {
        "title": "A República",
        "author": "Platão",
        "translator": "Heleno Salgado",
        "publisher": "OpenSciMD",
        "license": "Domínio Público",
    }
    colophon = generate_colophon_markdown(meta)
    assert "OpenSciMD" in colophon
    assert "Platão" in colophon
    assert "Heleno Salgado" in colophon
    assert "colophon-box" in colophon


def test_generate_frontmatter_editorial_blocks():
    meta = {
        "title": "Apologia de Sócrates",
        "author": "Platão",
        "translator": "Heleno Salgado",
        "publisher": "OpenSciMD",
        "license": "Domínio Público",
        "date": "399 a.C.",
        "categories": ["Filosofia"],
    }
    blocks = generate_frontmatter_editorial_blocks(meta)
    assert "editorial-titlepage" in blocks
    assert "catalographic-box" in blocks
    assert "399 a.C." in blocks
    assert "Traduzido por Heleno Salgado" in blocks
    assert "Tradução e notas por" not in blocks
    assert "publisher-brand" not in blocks


def test_generate_institutional_page():
    page_md = generate_institutional_page()
    assert "institutional-card" in page_md
    assert "OpenSciMD &amp; Leia-me" in page_md
    assert "leiame.app" in page_md
    assert "CC BY-NC-ND 4.0" in page_md
    assert "Salgado, H. (2026). OpenSciMD: Open-Access Scientific Articles in Markdown (Version 1.1.0) [Data set]." in page_md
    assert "https://github.com/HelenoSalgado/openscimd" in page_md


def test_epub_css_kindle_compliance():
    css_path = Path("scripts/templates/epub.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")
    
    # h2 não pode forçar quebra de página
    assert "page-break-before: auto;" in content
    assert "break-before: auto;" in content
    assert "h2 {" in content
    # citation-box deve ter cor explícita e regras dark mode
    assert ".citation-box" in content
    assert "color: #2D3748;" in content
    assert "@media (prefers-color-scheme: dark)" in content



def test_find_cover_image_not_found(tmp_path):
    dummy_book = tmp_path / "dummy-book.md"
    dummy_book.write_text("# Teste", encoding="utf-8")
    assert find_cover_image(dummy_book, tmp_path) is None


def test_find_cover_image_found(tmp_path):
    covers_dir = tmp_path / "assets" / "covers" / "originals"
    covers_dir.mkdir(parents=True)
    cover_file = covers_dir / "obra-antiga.png"
    cover_file.write_bytes(b"dummy image data")

    dummy_book = tmp_path / "content" / "books" / "obra-antiga.md"
    dummy_book.parent.mkdir(parents=True)
    dummy_book.write_text("# Teste", encoding="utf-8")

    found = find_cover_image(dummy_book, tmp_path)
    assert found == cover_file


def test_convert_md_to_epub_success(tmp_path):
    book_file = tmp_path / "livro-teste.md"
    book_file.write_text(
        """---
title: "Livro de Exemplo"
author: "Pensador Notável"
translator: "Heleno Salgado"
language: "pt-BR"
summary: "Um resumo conciso sobre o exemplar."
---

## Capítulo Primeiro

Este é o início do texto editorial.

### Subseção Dialética

Argumentação lógica e coerente.
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
    assert res_path == out_epub
    assert res_path.stat().st_size > 0

    # Validar integridade da estrutura EPUB (ZIP)
    with zipfile.ZipFile(res_path, "r") as z:
        namelist = z.namelist()
        assert "mimetype" in namelist
        assert "META-INF/container.xml" in namelist
        
        # Verificar metadados Dublin Core dentro do content.opf
        opf_name = next(name for name in namelist if name.endswith(".opf"))
        opf_content = z.read(opf_name).decode("utf-8")
        assert "Livro de Exemplo" in opf_content
        assert "Pensador Notável" in opf_content
        assert "OpenSciMD" in opf_content


def test_convert_md_to_epub_missing_file():
    with pytest.raises(FileNotFoundError):
        convert_md_to_epub("arquivo_totalmente_inexistente.md")


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

    # 1. Estruturado (padrão)
    resolved = resolve_epub_output_path(books_file, project_root, structured=True)
    expected = project_root / "dist" / "content" / "books" / "platao" / "dialogo.epub"
    assert resolved == expected

    # 2. Flat
    resolved_flat = resolve_epub_output_path(books_file, project_root, structured=False)
    expected_flat = project_root / "dist" / "dialogo.epub"
    assert resolved_flat == expected_flat

    # 3. Customizado explícito
    custom_target = tmp_path / "custom" / "livro.epub"
    resolved_custom = resolve_epub_output_path(books_file, project_root, output_epub_path=custom_target)
    assert resolved_custom == custom_target


def test_batch_convert_content(tmp_path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    book = project_root / "content" / "books" / "autor1" / "obra.md"
    book.parent.mkdir(parents=True)
    book.write_text("---\ntitle: 'Obra 1'\nauthor: 'Autor 1'\n---\n\n## Cap 1\n\nConteúdo.")

    art = project_root / "content" / "articles" / "rev1" / "artigo.md"
    art.parent.mkdir(parents=True)
    art.write_text("---\ntitle: 'Artigo 1'\nauthor: 'Autor 2'\n---\n\n## Introdução\n\nTexto.")

    # Executar batch
    res = batch_convert_content(base_dir=project_root)
    assert res["total"] == 2
    assert len(res["succeeded"]) == 2
    assert len(res["failed"]) == 0

    expected_book_epub = project_root / "dist" / "content" / "books" / "autor1" / "obra.epub"
    expected_art_epub = project_root / "dist" / "content" / "articles" / "rev1" / "artigo.epub"
    assert expected_book_epub.exists()
    assert expected_art_epub.exists()


def test_cli_build_epub_all_and_validate_kindle(tmp_path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    book = project_root / "content" / "books" / "platao" / "fedro.md"
    book.parent.mkdir(parents=True)
    book.write_text("---\ntitle: 'Fedro'\nauthor: 'Platão'\n---\n\n## Discurso\n\nSobre a retórica.")

    # CLI sem argumentos deve falhar avisando sobre --all ou arquivo
    res_err = runner.invoke(app, ["build-epub"])
    assert res_err.exit_code == 1
    assert "Forneça o caminho do arquivo Markdown ou utilize a flag '--all'" in res_err.stdout

    try:
        # Compilar livro com estrutura padrão
        res_build = runner.invoke(app, ["build-epub", str(book)])
        assert res_build.exit_code == 0
        generated_epub = Path("dist/content/books/platao/fedro.epub")
        assert generated_epub.exists()

        # Validar Kindle via CLI
        res_val = runner.invoke(app, ["validate-kindle", str(generated_epub)])
        assert res_val.exit_code == 0
        assert "APROVADO" in res_val.stdout
    finally:
        generated_epub = Path("dist/content/books/platao/fedro.epub")
        if generated_epub.exists():
            generated_epub.unlink()
        # Limpar diretórios pais se vazios
        if generated_epub.parent.exists() and not any(generated_epub.parent.iterdir()):
            generated_epub.parent.rmdir()
