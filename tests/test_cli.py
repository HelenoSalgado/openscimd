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
