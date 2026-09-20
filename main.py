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

@app.command(name="clean-html")
def clean_html_cmd(
    input_file: str = typer.Argument(..., help="Caminho do arquivo HTML legado para conversão."),
    output_file: str = typer.Argument(..., help="Caminho do arquivo Markdown de saída."),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Título customizado para o documento."),
):
    """Converte HTML legado de layout antigo para Markdown limpo com citações semânticas."""
    from scripts.html_cleaner import LegacyHtmlCleaner
    try:
        out = LegacyHtmlCleaner.convert_file(input_file, output_file, part_title=title)
        typer.secho(f"✅ HTML convertido com sucesso em: {out}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao converter HTML legado: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command(name="assemble-book")
def assemble_book_cmd(
    parts_dir: str = typer.Argument(..., help="Diretório contendo as partes Markdown revisadas."),
    output_file: str = typer.Argument(..., help="Caminho do arquivo de livro Markdown compilado."),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Título do volume."),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Autor do volume."),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Resumo do volume."),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Data canônica da obra."),
    license_: Optional[str] = typer.Option(None, "--license", "-l", help="Licença editorial."),
):
    """Monta um volume canônico a partir de partes modulares revisadas."""
    from scripts.book_assembler import BookAssembler
    metadata = {}
    if title: metadata["title"] = title
    if author: metadata["author"] = author
    if summary: metadata["summary"] = summary
    if date: metadata["date"] = date
    if license_: metadata["license"] = license_
    try:
        out = BookAssembler.assemble_volume(parts_dir, output_file, metadata)
        typer.secho(f"✅ Volume compilado com sucesso em: {out}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao compilar volume: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

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
    from scripts.text_tools import converter_versiculos
    converter_versiculos(input_file, output_file)

@app.command()
def review(
    filepath: str = typer.Argument(..., help="Caminho do arquivo ou diretório Markdown para revisão."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho do arquivo de saída revisado (preserva o original)."),
    dict_path: Optional[str] = typer.Option(None, "--dict", "-d", help="Caminho para dicionário JSON customizado."),
    auto_apply: bool = typer.Option(False, "--auto-fix", "--auto-apply", "-y", help="Aplica todas as substituições conhecidas automaticamente."),
    dry_run: bool = typer.Option(False, "--check", "--dry-run", help="Modo verificação: lista arcaísmos e erros sem alterar os arquivos."),
    no_hunspell: bool = typer.Option(False, "--no-hunspell", help="Desativa a detecção morfológica via Hunspell."),
    backup: bool = typer.Option(False, "--backup", "-b", help="Cria backup .bak antes de sobrescrever o arquivo."),
):
    """Revisor ortográfico e de arcaísmos de alta performance (Dicionário Curado + Hunspell pt_BR)."""
    from scripts.spellchecker import review_path
    review_path(
        filepath,
        output_path=output,
        dict_path=dict_path,
        auto_apply=auto_apply,
        dry_run=dry_run,
        backup=backup,
        use_hunspell=not no_hunspell,
    )

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
    from scripts.text_tools import normalize_biblical_refs
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
        
@app.command(name="export-pdf")
def export_pdf_cmd(
    input_file: str = typer.Argument(..., help="Caminho do arquivo Markdown para conversão."),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho do PDF de saída (opcional).")
):
    """Converte um documento Markdown para PDF com design editorial elegante e paleta LeiaME."""
    try:
        from scripts.md2pdf import convert_md_to_pdf
        in_path = Path(input_file)
        if not output_file:
            out_path = in_path.with_suffix(".pdf")
        else:
            out_path = Path(output_file)
            
        convert_md_to_pdf(str(in_path), str(out_path))
        typer.secho(f"✅ PDF gerado com sucesso: {out_path}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Erro ao exportar PDF: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
