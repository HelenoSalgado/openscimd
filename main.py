import os
from pathlib import Path
from typing import Optional
import typer

# Import the modules
# from scripts.assets import convert_assets
# from scripts.covers import convert_covers, inject_cover_text
# from scripts.html2md import convert_html_to_md
# from scripts.ai_cover import generate_cover
from scripts.indexer import update_index, update_articles_index, update_books_index
# from scripts.validator import validate_articles
# from scripts.text_tools import converter_versiculos, spellcheck, normalize_biblical_refs
# from scripts.enricher import enrich_metadata

app = typer.Typer(help="OpenSciMD CLI para gerenciamento de artigos e livros.")

BASE_DIR = Path(__file__).resolve().parent

@app.command()
def build_assets():
    """Converte e redimensiona os assets de imagens."""
    from scripts.assets import convert_assets
    convert_assets(str(BASE_DIR))

@app.command()
def build_covers(
    target_file: Optional[str] = typer.Option(None, "--target", "-t", help="Arquivo específico de capa para converter."),
    force: bool = typer.Option(False, "--force", "-f", help="Força a conversão sobrescrevendo mesmo se os arquivos já estiverem atualizados.")
):
    """Converte e redimensiona capas de livros."""
    from scripts.covers import convert_covers
    convert_covers(str(BASE_DIR), target_file=target_file, force=force)

@app.command()
def inject_text(image_path: str, custom_text: Optional[str] = None):
    """Injeta texto em capas brutas (tipografia)."""
    from scripts.covers import inject_cover_text
    inject_cover_text(str(BASE_DIR), image_path, custom_text)

@app.command()
def html_to_md(input_file: str, output_file: str):
    """Converte HTML exportado para Markdown com Frontmatter YAML."""
    from scripts.html2md import convert_html_to_md
    convert_html_to_md(str(BASE_DIR), input_file, output_file)

@app.command()
def ai_cover(article_name: str, custom_style: Optional[str] = None, provider: str = "gemini"):
    """Gera uma arte de capa conceitual com IA e tipografia vetorial (gemini, openai ou agy)."""
    from scripts.ai_cover import generate_cover
    generate_cover(str(BASE_DIR), article_name, custom_style, provider)

@app.command()
def index():
    """Atualiza o JSON index de artigos e livros."""
    update_index(str(BASE_DIR))

@app.command()
def validate():
    """Valida formato e metadados de artigos MD."""
    from scripts.validator import validate_articles
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
        from scripts.salopdoc_adapter import import_pdf
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
        from scripts.salopdoc_adapter import batch_import
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
        from scripts.salopdoc_adapter import clean_markdown_file
        out = clean_markdown_file(file_path=file_path, output_path=output_path)
        typer.secho(f"✅ Markdown normalizado com sucesso: {out}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao normalizar Markdown: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def normalize_refs(
    filepath: str = typer.Argument(..., help="Caminho do arquivo Markdown."),
    sep: str = typer.Option(".", "--sep", "-s", help="Separador alvo (ex: '.' ou ':'). Padrão: '.'"),
    pattern: str = typer.Option(None, "--pattern", "-p", help="Padrão Regex (opcional). Se omitido, usa lista segura de livros."),
    replacement: str = typer.Option(None, "--replacement", "-r", help="Substituição Regex (opcional).")
):
    """Padroniza referências bíblicas (ex: 3:16 para 3.16 ou 3,16 para 3:16) via Expressão Regular."""
    normalize_biblical_refs(filepath, sep, pattern, replacement)

@app.command()
def enrich(
    filepath: str = typer.Argument(..., help="Caminho do arquivo Markdown para enriquecer metadados.")
):
    """Busca metadados na API do Crossref com base no DOI presente no Frontmatter."""
    from scripts.enricher import enrich_metadata
    enrich_metadata(filepath)

@app.command()
def check_translation(
    english_file: str = typer.Argument(..., help="Arquivo de texto original em Inglês."),
    pt_file: str = typer.Argument(None, help="Arquivo de texto opcional com a tradução em PT para avaliar.")
):
    """Avalia a fidelidade semântica de uma tradução usando MarianMT e Back-Translation."""
    from scripts.fidelity_checker import test_fidelity
    
    with open(english_file, 'r', encoding='utf-8') as f:
        en_text = f.read().strip()
        
    pt_text = None
    if pt_file and os.path.exists(pt_file):
        with open(pt_file, 'r', encoding='utf-8') as f:
            pt_text = f.read().strip()
            
    test_fidelity(en_text, pt_text)

@app.command()
def pipeline_review(
    raw_en_file: str = typer.Argument(..., help="Arquivo Inglês original."),
    pt_file: str = typer.Argument(..., help="Arquivo PT traduzido."),
    limit: int = typer.Option(None, "--limit", "-l", help="Limite de linhas ou parágrafos para testes."),
    start: int = typer.Option(None, "--start", "-s", help="Índice do bloco inicial (1-based)."),
    end: int = typer.Option(None, "--end", "-e", help="Índice do bloco final (1-based).")
):
    """Gera um relatório de fidelidade extraindo blocos de texto puros de qualquer formato Markdown."""
    from scripts.alignment_pipeline import run_alignment_and_report
    run_alignment_and_report(raw_en_file, pt_file, limit=limit, start=start, end=end)

@app.command()
def translate_file(
    input_file: str = typer.Argument(..., help="Arquivo em Inglês para traduzir."),
    output_file: str = typer.Argument(..., help="Caminho para salvar a tradução em PT.")
):
    """Traduz um documento do Inglês para o Português linha a linha usando MarianMT."""
    from scripts.fidelity_checker import get_models, translate
    from tqdm import tqdm
    
    print("Carregando modelos MarianMT...")
    tokenizer_en_pt, model_en_pt, _, _ = get_models()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    translated_lines = []
    for line in tqdm(lines, desc="Traduzindo documento"):
        stripped = line.strip()
        # Pular YAML e linhas vazias
        if not stripped or stripped == '---' or stripped.startswith('title:') or stripped.startswith('author:'):
            translated_lines.append(line)
            continue
            
        pt_text = translate(stripped, tokenizer_en_pt, model_en_pt)
        # Tenta preservar a formatação de espaço original
        translated_lines.append(line.replace(stripped, pt_text))
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(translated_lines)
        
    print(f"\n✅ Tradução salva em: {output_file}")

if __name__ == "__main__":
    app()
