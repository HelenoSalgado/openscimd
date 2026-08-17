import os
from pathlib import Path
from typing import Optional
import typer

# Import the modules
from scripts.assets import convert_assets
from scripts.covers import convert_covers, inject_cover_text
from scripts.html2md import convert_html_to_md
from scripts.ai_cover import generate_cover
from scripts.indexer import update_index, update_articles_index, update_books_index
from scripts.validator import validate_articles
from scripts.text_tools import converter_versiculos, spellcheck
from scripts.salopdoc_adapter import import_pdf, batch_import, clean_markdown_file

app = typer.Typer(help="OpenSciMD CLI para gerenciamento de artigos e livros.")

BASE_DIR = Path(__file__).resolve().parent

@app.command()
def build_assets():
    """Converte e redimensiona os assets de imagens."""
    convert_assets(str(BASE_DIR))

@app.command()
def build_covers(
    target_file: Optional[str] = typer.Option(None, "--target", "-t", help="Arquivo específico de capa para converter."),
    force: bool = typer.Option(False, "--force", "-f", help="Força a conversão sobrescrevendo mesmo se os arquivos já estiverem atualizados.")
):
    """Converte e redimensiona capas de livros."""
    convert_covers(str(BASE_DIR), target_file=target_file, force=force)

@app.command()
def inject_text(image_path: str, custom_text: Optional[str] = None):
    """Injeta texto em capas brutas (tipografia)."""
    inject_cover_text(str(BASE_DIR), image_path, custom_text)

@app.command()
def html_to_md(input_file: str, output_file: str):
    """Converte HTML exportado para Markdown com Frontmatter YAML."""
    convert_html_to_md(str(BASE_DIR), input_file, output_file)

@app.command()
def ai_cover(article_name: str, custom_style: Optional[str] = None, provider: str = "gemini"):
    """Gera uma arte de capa com IA (gemini ou openai)."""
    generate_cover(str(BASE_DIR), article_name, custom_style, provider)

@app.command()
def index():
    """Atualiza o JSON index de artigos e livros."""
    update_index(str(BASE_DIR))

@app.command()
def validate():
    """Valida formato e metadados de artigos MD."""
    if not validate_articles(str(BASE_DIR)):
        raise typer.Exit(code=1)

@app.command()
def verses(input_file: str, output_file: str):
    """Converte números de início de linha para versículos sobrescritos."""
    converter_versiculos(input_file, output_file)

@app.command()
def review(filepath: str, dict_path: Optional[str] = None):
    """Revisor ortográfico interativo para arcaísmos."""
    spellcheck(filepath, dict_path)

@app.command(name="import-pdf")
def import_pdf_cmd(
    pdf_path: str = typer.Argument(..., help="Caminho do arquivo PDF para conversão."),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho do Markdown de saída."),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Título customizado para o frontmatter."),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Autor customizado para o frontmatter."),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Data customizada (YYYY-MM-DD)."),
):
    """Converte um documento PDF em Markdown rico com Frontmatter YAML via SalopDoc."""
    try:
        out = import_pdf(
            pdf_path=pdf_path,
            output_path=output_path,
            base_dir=BASE_DIR,
            title=title,
            author=author,
            date=date,
        )
        typer.secho(f"✅ Artigo convertido com sucesso: {out}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao converter PDF: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command(name="batch-import")
def batch_import_cmd(
    input_dir: Optional[str] = typer.Option(None, "--input-dir", "-i", help="Diretório de entrada com PDFs brutos."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Diretório de saída para os rascunhos MD."),
):
    """Processa todos os PDFs de um diretório em lote via SalopDoc."""
    try:
        batch_import(
            input_dir=input_dir,
            output_dir=output_dir,
            base_dir=BASE_DIR,
        )
    except Exception as e:
        typer.secho(f"❌ Erro no processamento em lote: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command(name="clean-md")
def clean_md_cmd(
    file_path: str = typer.Argument(..., help="Caminho do arquivo Markdown a ser normalizado."),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho de saída opcional."),
):
    """Normaliza a tipografia, aspas e estrutura de cabeçalhos de um Markdown existente."""
    try:
        out = clean_markdown_file(file_path=file_path, output_path=output_path)
        typer.secho(f"✅ Markdown normalizado com sucesso: {out}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao normalizar Markdown: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
