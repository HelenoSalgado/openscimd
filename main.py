import os
import typer
from pathlib import Path

# Impor the modules
from scripts.assets import convert_assets
from scripts.covers import convert_covers, inject_cover_text
from scripts.html2md import convert_html_to_md
from scripts.ai_cover import generate_cover
from scripts.indexer import update_index, update_articles_index, update_books_index
from scripts.validator import validate_articles
from scripts.text_tools import converter_versiculos, spellcheck

app = typer.Typer(help="OpenSciMD CLI para gerenciamento de artigos e livros.")

BASE_DIR = Path(__file__).resolve().parent

@app.command()
def build_assets():
    """Converte e redimensiona os assets de imagens."""
    convert_assets(str(BASE_DIR))

@app.command()
def build_covers(
    target_file: str = typer.Option(None, "--target", "-t", help="Arquivo específico de capa para converter."),
    force: bool = typer.Option(False, "--force", "-f", help="Força a conversão sobrescrevendo mesmo se os arquivos já estiverem atualizados.")
):
    """Converte e redimensiona capas de livros."""
    convert_covers(str(BASE_DIR), target_file=target_file, force=force)

@app.command()
def inject_text(image_path: str, custom_text: str = None):
    """Injeta texto em capas brutas (tipografia)."""
    inject_cover_text(str(BASE_DIR), image_path, custom_text)

@app.command()
def html_to_md(input_file: str, output_file: str):
    """Converte HTML exportado para Markdown com Frontmatter YAML."""
    convert_html_to_md(str(BASE_DIR), input_file, output_file)

@app.command()
def ai_cover(article_name: str, custom_style: str = None, provider: str = "gemini"):
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
def review(filepath: str, dict_path: str = None):
    """Revisor ortográfico interativo para arcaísmos."""
    spellcheck(filepath, dict_path)

if __name__ == "__main__":
    app()
