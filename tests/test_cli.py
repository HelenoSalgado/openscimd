from typer.testing import CliRunner
from main import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "OpenSciMD CLI para gerenciamento de artigos e livros." in result.stdout
    assert "import-pdf" in result.stdout
    assert "batch-import" in result.stdout
    assert "clean-md" in result.stdout


def test_cli_clean_md(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Article\n\nSome text with \"quotes\".\n", encoding="utf-8")
    
    out_file = tmp_path / "cleaned.md"
    result = runner.invoke(app, ["clean-md", str(md_file), "--output", str(out_file)])
    assert result.exit_code == 0
    assert "Markdown normalizado com sucesso" in result.stdout
    assert out_file.exists()


def test_cli_import_pdf_missing_file():
    result = runner.invoke(app, ["import-pdf", "non_existent_file.pdf"])
    assert result.exit_code != 0
    assert "Erro ao converter PDF" in result.stdout


def test_cli_clean_html(tmp_path):
    html_file = tmp_path / "test.htm"
    html_file.write_text("<html><body><h3>Título</h3><p>Parágrafo de teste.</p></body></html>", encoding="utf-8")
    out_file = tmp_path / "out.md"
    result = runner.invoke(app, ["clean-html", str(html_file), str(out_file), "--title", "Título Customizado"])
    assert result.exit_code == 0
    assert "HTML convertido com sucesso" in result.stdout
    assert out_file.exists()


def test_cli_assemble_book(tmp_path):
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()
    (parts_dir / "01-cap.md").write_text("---\ntitle: Cap 1\n---\nTexto", encoding="utf-8")
    out_book = tmp_path / "book.md"
    result = runner.invoke(app, ["assemble-book", str(parts_dir), str(out_book), "--title", "Livro Teste"])
    assert result.exit_code == 0
    assert "Volume compilado com sucesso" in result.stdout
    assert out_book.exists()
