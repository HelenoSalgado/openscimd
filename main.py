from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import cast

import typer

from scripts.indexer import update_index

app = typer.Typer(help="OpenSciMD CLI para gerenciamento de artigos e livros.")

BASE_DIR = Path(__file__).resolve().parent

_PANEL_INGEST = "1. Ingestão & Conversão"
_PANEL_REVIEW = "2. Revisão & Edição"
_PANEL_VALIDATE = "3. Validação & Gates"
_PANEL_PUBLISH = "4. Publicação & Catálogo"
_PANEL_COVERS = "5. Capas & Mídia"
_PANEL_EXPORT = "6. Exportação & RAG"
_PANEL_TRANSLATE = "7. Tradução (Experimental / Em Redesign)"


# ── 1. Ingestão & Conversão ────────────────────────────────────────────────────


@app.command(name="import-pdf", rich_help_panel=_PANEL_INGEST)
def import_pdf_cmd(
    pdf_path: str = typer.Argument(..., help="Caminho do arquivo PDF para conversão."),
    output_path: str | None = typer.Option(None, "--output", "-o", help="Caminho do Markdown de saída."),
    title: str | None = typer.Option(None, "--title", "-t", help="Título customizado para o frontmatter."),
    author: str | None = typer.Option(None, "--author", "-a", help="Autor customizado para o frontmatter."),
    date: str | None = typer.Option(None, "--date", "-d", help="Data customizada (YYYY-MM-DD)."),
) -> None:
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
    except Exception as exc:
        typer.secho(f"❌ Erro ao converter PDF: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="batch-import", rich_help_panel=_PANEL_INGEST)
def batch_import_cmd(
    input_dir: str | None = typer.Option(None, "--input-dir", "-i", help="Diretório de entrada com PDFs brutos."),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Diretório de saída para os rascunhos MD."),
) -> None:
    """Processa todos os PDFs de um diretório em lote via SalopDoc."""
    try:
        from scripts.salopdoc_adapter import batch_import

        batch_import(
            input_dir=input_dir,
            output_dir=output_dir,
            base_dir=BASE_DIR,
        )
    except Exception as exc:
        typer.secho(f"❌ Erro no processamento em lote: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="remote-extract", rich_help_panel=_PANEL_INGEST)
def remote_extract_cmd(
    pdf_path: str = typer.Argument(..., help="Caminho do PDF escaneado em data/raw/"),
    output_dir: str = typer.Option("data/draft", "--output-dir", "-o", help="Diretório de saída para os rascunhos MD."),
    gpu_type: str = typer.Option("T4", "--gpu", "-g", help="Tipo de acelerador GPU (T4, L4, A100)."),
    lang: str = typer.Option("latin", "--lang", "-l", help="Idioma/alfabeto OCR (latin, en, etc.)."),
    session_name: str | None = typer.Option(None, "--session", "-s", help="Nome da sessão remota no Colab."),
    keep_alive: bool = typer.Option(
        False, "--keep-alive", help="Manter a sessão ativa após a conclusão (para processamento em lote)."
    ),
) -> None:
    """Extrai PDF escaneado remotamente em GPU no Google Colab via saloppdf e SSH."""
    from scripts.colab_runner import DEFAULT_SESSION, execute_remote_extraction

    try:
        pdf_file = Path(pdf_path).resolve()
        out_path = Path(output_dir).resolve()
        sess = session_name or DEFAULT_SESSION

        res = execute_remote_extraction(
            pdf_path=pdf_file,
            output_dir=out_path,
            session_name=sess,
            gpu_type=gpu_type,
            lang=lang,
            keep_alive=keep_alive,
        )
        typer.secho(f"✅ Extração remota finalizada com sucesso: {res}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"❌ Erro na extração remota: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="clean-html", rich_help_panel=_PANEL_INGEST)
def clean_html_cmd(
    input_file: str = typer.Argument(..., help="Caminho do arquivo HTML legado para conversão."),
    output_file: str = typer.Argument(..., help="Caminho do arquivo Markdown de saída."),
    title: str | None = typer.Option(None, "--title", "-t", help="Título customizado para o documento."),
    author: str | None = typer.Option(None, "--author", "-a", help="Autor da obra para o frontmatter YAML."),
) -> None:
    """Converte HTML legado de layout antigo para Markdown limpo com citações semânticas."""
    from scripts.html_cleaner import LegacyHtmlCleaner

    try:
        out = LegacyHtmlCleaner.convert_file(input_file, output_file, part_title=title, author=author)
        typer.secho(f"✅ HTML convertido com sucesso em: {out}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"❌ Erro ao converter HTML legado: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(rich_help_panel=_PANEL_INGEST)
def html_to_md(input_file: str, output_file: str) -> None:
    """Converte HTML exportado para Markdown com Frontmatter YAML."""
    from scripts.html2md import convert_html_to_md

    convert_html_to_md(str(BASE_DIR), input_file, output_file)


@app.command(name="clean-md", rich_help_panel=_PANEL_INGEST)
def clean_md_cmd(
    file_path: str = typer.Argument(..., help="Caminho do arquivo Markdown a ser normalizado."),
    output_path: str | None = typer.Option(None, "--output", "-o", help="Caminho de saída opcional."),
) -> None:
    """Normaliza a tipografia, aspas e estrutura de cabeçalhos de um Markdown existente."""
    try:
        from scripts.salopdoc_adapter import clean_markdown_file

        out = clean_markdown_file(file_path=file_path, output_path=output_path)
        typer.secho(f"✅ Markdown normalizado com sucesso: {out}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"❌ Erro ao normalizar Markdown: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="assemble-book", rich_help_panel=_PANEL_INGEST)
def assemble_book_cmd(
    parts_dir: str = typer.Argument(..., help="Diretório contendo as partes Markdown revisadas."),
    output_file: str = typer.Argument(..., help="Caminho do arquivo de livro Markdown compilado."),
    title: str | None = typer.Option(None, "--title", "-t", help="Título do volume."),
    author: str | None = typer.Option(None, "--author", "-a", help="Autor do volume."),
    summary: str | None = typer.Option(None, "--summary", "-s", help="Resumo do volume."),
    date: str | None = typer.Option(None, "--date", "-d", help="Data canônica da obra."),
    license_: str | None = typer.Option(None, "--license", "-l", help="Licença editorial."),
    preset: str | None = typer.Option(None, "--preset", help="Preset editorial opcional (ex.: 'hugo-vitor')."),
    no_default_notes: bool = typer.Option(False, "--no-default-notes", help="Desativa notas editoriais automáticas."),
) -> None:
    """Monta um volume canônico a partir de partes modulares revisadas."""
    from scripts.book_assembler import BookAssembler

    metadata: dict[str, str] = {}
    if title:
        metadata["title"] = title
    if author:
        metadata["author"] = author
    if summary:
        metadata["summary"] = summary
    if date:
        metadata["date"] = date
    if license_:
        metadata["license"] = license_
    try:
        out = BookAssembler.assemble_volume(
            parts_dir,
            output_file,
            metadata,
            add_default_editorial_notes=not no_default_notes,
            preset=preset,
        )
        typer.secho(f"✅ Volume compilado com sucesso em: {out}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"❌ Erro ao compilar volume: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


# ── 2. Revisão & Edição ────────────────────────────────────────────────────────


@app.command(name="start-review", rich_help_panel=_PANEL_REVIEW)
def start_review_cmd(
    source: str = typer.Argument(..., help="Arquivo de origem em data/draft/ ou obra publicada em content/."),
    dest: str | None = typer.Option(
        None, "--dest", "-d", help="Subcaminho relativo de destino em data/review/<type>/."
    ),
    doc_type: str | None = typer.Option(None, "--type", "-t", help="Tipo de obra: 'articles' ou 'books'."),
    no_audit: bool = typer.Option(False, "--no-audit", help="Não gera manifesto .audit.md de blocos."),
    overwrite: bool = typer.Option(False, "--overwrite", "-f", help="Sobrescreve cópia existente em data/review/."),
) -> None:
    """Inicia mesa de revisão ativa em data/review/ copiando rascunho ou obra publicada."""
    from scripts.workflow import ReviewDocType, WorkflowError, start_review

    if doc_type is not None and doc_type not in ("articles", "books"):
        typer.secho("❌ '--type' deve ser 'articles' ou 'books'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typed_doc: ReviewDocType | None = cast(ReviewDocType, doc_type) if doc_type else None
    try:
        res = start_review(
            source_path=source,
            base_dir=BASE_DIR,
            dest_rel=dest,
            doc_type=typed_doc,
            create_audit=not no_audit,
            overwrite=overwrite,
        )
        typer.secho(f"✅ Revisão iniciada em: {res.review_path}", fg=typer.colors.GREEN)
        if res.audit_path:
            typer.secho(
                f"📋 Manifesto criado: {res.audit_path} ({res.total_lines} linhas, {res.block_count} bloco(s))",
                fg=typer.colors.CYAN,
            )
    except (FileNotFoundError, FileExistsError, WorkflowError) as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(rich_help_panel=_PANEL_REVIEW)
def enrich(
    filepath: str = typer.Argument(..., help="Caminho do arquivo Markdown para enriquecer metadados."),
) -> None:
    """Busca metadados na API do Crossref/Zenodo com base no DOI presente no Frontmatter."""
    from scripts.enricher import enrich_metadata

    enrich_metadata(filepath)


@app.command(rich_help_panel=_PANEL_REVIEW)
def normalize_refs(
    filepath: str = typer.Argument(..., help="Caminho do arquivo Markdown."),
    sep: str = typer.Option(".", "--sep", "-s", help="Separador alvo (ex: '.' ou ':'). Padrão: '.'"),
    pattern: str | None = typer.Option(None, "--pattern", "-p", help="Padrão Regex (opcional)."),
    replacement: str | None = typer.Option(None, "--replacement", "-r", help="Substituição Regex (opcional)."),
    canonical: bool = typer.Option(
        True,
        "--canonical/--no-canonical",
        "-c",
        help="Padroniza variantes fora do padrão preservando extenso vs abreviado.",
    ),
    force_abbrev: bool = typer.Option(
        False,
        "--force-abbrev",
        help="Converte também nomes por extenso para abreviação canônica de 2 letras.",
    ),
    no_ranges: bool = typer.Option(False, "--no-ranges", help="Preserva hífen em intervalos de versículos."),
) -> None:
    """Padroniza referências bíblicas (ex: HB 11:1 -> Hb 11.1, João 3:16 -> João 3.16) em prosa."""
    from scripts.text_tools import normalize_biblical_refs

    normalize_biblical_refs(
        filepath,
        target_sep=sep,
        regex_pattern=pattern,
        replacement=replacement,
        canonical_abbrev=canonical,
        force_abbrev=force_abbrev,
        normalize_ranges=not no_ranges,
    )


@app.command(rich_help_panel=_PANEL_REVIEW)
def review(
    filepath: str = typer.Argument(..., help="Caminho do arquivo ou diretório Markdown para revisão."),
    output: str | None = typer.Option(None, "--output", "-o", help="Caminho do arquivo de saída revisado."),
    dict_path: str | None = typer.Option(None, "--dict", "-d", help="Caminho para dicionário JSON customizado."),
    auto_apply: bool = typer.Option(False, "--auto-fix", "--auto-apply", "-y", help="Aplica substituições conhecidas."),
    dry_run: bool = typer.Option(False, "--check", "--dry-run", help="Lista arcaísmos e erros sem alterar arquivos."),
    no_hunspell: bool = typer.Option(False, "--no-hunspell", help="Desativa a detecção morfológica via Hunspell."),
    backup: bool = typer.Option(False, "--backup", "-b", help="Cria backup .bak antes de sobrescrever."),
) -> None:
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


@app.command(rich_help_panel=_PANEL_REVIEW)
def verses(input_file: str, output_file: str) -> None:
    """Converte números de início de linha para versículos sobrescritos."""
    from scripts.text_tools import converter_versiculos

    converter_versiculos(input_file, output_file)


# ── 3. Validação & Gates ───────────────────────────────────────────────────────


@app.command(rich_help_panel=_PANEL_VALIDATE)
def validate(
    target: str = typer.Option("all", "--target", "-t", help="Alvo de validação: 'all', 'articles' ou 'books'."),
    file: str | None = typer.Option(None, "--file", "-f", help="Valida um único arquivo (YAML + linter editorial)."),
    source: str | None = typer.Option(None, "--source", "-s", help="Matriz local original para comparar com --file."),
    editorial: bool = typer.Option(False, "--editorial", help="Ativa também o linter editorial na validação global."),
    strict: bool = typer.Option(False, "--strict", help="Falha também quando houver alertas (warnings)."),
    translated: bool = typer.Option(
        False, "--translated", help="Usa faixas de comparação para tradução contra --source."
    ),
) -> None:
    """Valida formato, metadados e integridade editorial de artigos e e-books."""
    from scripts.validator import (
        print_file_validation_result,
        validate_all,
        validate_articles,
        validate_books,
        validate_single_file,
    )

    if file is not None:
        target_path = Path(file)
        if not target_path.is_absolute() and (BASE_DIR / target_path).exists():
            target_path = BASE_DIR / target_path
        if not target_path.is_file():
            typer.secho(f"❌ Arquivo não encontrado: {file}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        src_path = Path(source) if source else None
        if src_path and not src_path.is_absolute() and (BASE_DIR / src_path).exists():
            src_path = BASE_DIR / src_path

        res = validate_single_file(
            target_path,
            base_dir=BASE_DIR,
            check_editorial=True,
            check_assets=False,
            source_path=src_path,
            translated=translated,
            strict_language=True,
        )
        print_file_validation_result(res)
        if not res.is_valid(strict=strict):
            typer.secho(
                f"❌ Validação reprovada: {res.total_errors} erro(s), {res.total_warnings} alerta(s).",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
        typer.secho(
            f"✅ Arquivo aprovado! (0 erros, {res.total_warnings} alerta(s))",
            fg=typer.colors.GREEN,
        )
        return

    if target == "articles":
        success = validate_articles(str(BASE_DIR), check_editorial=editorial, strict=strict)
    elif target == "books":
        success = validate_books(str(BASE_DIR), check_editorial=editorial, strict=strict)
    else:
        success = validate_all(str(BASE_DIR), check_editorial=editorial, strict=strict)
    if not success:
        raise typer.Exit(code=1)


@app.command(name="lint", rich_help_panel=_PANEL_VALIDATE)
def lint_cmd(
    target_path: str = typer.Argument(..., help="Arquivo Markdown ou diretório para checagem editorial."),
    source: str | None = typer.Option(
        None, "--source", "-s", help="Matriz local original (apenas para arquivo único)."
    ),
    doc_type: str | None = typer.Option(None, "--type", "-t", help="Tipo opcional ('article' ou 'book')."),
    translated: bool = typer.Option(False, "--translated", help="Ajusta tolerância de extensão para obra traduzida."),
    strict: bool = typer.Option(False, "--strict", help="Retorna código de erro também em alertas (warnings)."),
    with_metadata: bool = typer.Option(False, "--with-metadata", help="Inclui validação completa de metadados YAML."),
) -> None:
    """Executa o linter editorial determinístico em um arquivo ou diretório."""
    from scripts.editorial_linter import lint_markdown_file
    from scripts.utils import get_files_recursively
    from scripts.validator import DocType, print_file_validation_result, validate_single_file

    target = Path(target_path)
    if not target.is_absolute() and (BASE_DIR / target).exists():
        target = BASE_DIR / target

    if not target.exists():
        typer.secho(f"❌ Caminho não encontrado: {target_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if doc_type is not None and doc_type not in ("article", "book"):
        typer.secho("❌ '--type' deve ser 'article' ou 'book'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typed_doc: DocType | None = cast(DocType, doc_type) if doc_type else None

    if target.is_file():
        src_path = Path(source) if source else None
        if src_path and not src_path.is_absolute() and (BASE_DIR / src_path).exists():
            src_path = BASE_DIR / src_path

        if with_metadata:
            res = validate_single_file(
                target,
                base_dir=BASE_DIR,
                doc_type=typed_doc,
                check_editorial=True,
                source_path=src_path,
                translated=translated,
                strict_language=True,
            )
            print_file_validation_result(res)
            if not res.is_valid(strict=strict):
                raise typer.Exit(code=1)
            typer.secho("✅ Lint + metadados aprovados!", fg=typer.colors.GREEN)
            return

        report = lint_markdown_file(target, source_path=src_path, translated=translated)
        for issue in report.all_issues:
            line_tag = f"L{issue.line}" if issue.line is not None else "Geral"
            prefix = "❌ [ERRO" if issue.severity == "error" else "⚠️ [ALERTA"
            typer.echo(f"  {prefix} {issue.code} @ {line_tag}] {issue.message}")

        err_count = len(report.errors)
        warn_count = len(report.warnings)
        if err_count > 0 or (strict and warn_count > 0):
            typer.secho(
                f"❌ Linter reprovado: {err_count} erro(s), {warn_count} alerta(s).",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
        typer.secho(f"✅ Linter aprovado: 0 erros, {warn_count} alerta(s).", fg=typer.colors.GREEN)
        return

    md_files = [Path(p) for p in get_files_recursively(target)]
    if not md_files:
        typer.secho(f"⚠️ Nenhum arquivo .md encontrado em: {target}", fg=typer.colors.YELLOW)
        return

    code_counts: Counter[str] = Counter()
    total_errors = 0
    total_warnings = 0
    files_with_errors = 0

    for md_file in md_files:
        rel = md_file.relative_to(target).as_posix()
        if with_metadata:
            res = validate_single_file(
                md_file,
                base_dir=BASE_DIR,
                doc_type=typed_doc,
                check_editorial=True,
                strict_language=False,
            )
            print_file_validation_result(res, label=rel)
            file_errs = res.total_errors
            file_warns = res.total_warnings
            for issue in res.all_editorial_issues:
                code_counts[issue.code] += 1
        else:
            report = lint_markdown_file(md_file)
            file_errs = len(report.errors)
            file_warns = len(report.warnings)
            for issue in report.all_issues:
                code_counts[issue.code] += 1
            if report.all_issues:
                typer.echo(f"📄 {rel}: {file_errs} erro(s), {file_warns} alerta(s)")
                for issue in report.all_issues[:8]:
                    line_tag = f"L{issue.line}" if issue.line is not None else "Geral"
                    prefix = "❌" if issue.severity == "error" else "⚠️"
                    typer.echo(f"   {prefix} [{issue.code} @ {line_tag}] {issue.message}")
                if len(report.all_issues) > 8:
                    typer.echo(f"   ... (+{len(report.all_issues) - 8} ocorrência(s))")

        if file_errs > 0 or (strict and file_warns > 0):
            files_with_errors += 1
        total_errors += file_errs
        total_warnings += file_warns

    typer.echo("-" * 50)
    typer.echo(f"📊 Resumo Linter ({len(md_files)} arquivo(s)):")
    typer.echo(f"   - Arquivos com pendências bloqueantes: {files_with_errors}")
    typer.echo(f"   - Total de Erros: {total_errors}")
    typer.echo(f"   - Total de Alertas: {total_warnings}")
    if code_counts:
        typer.echo("   - Ocorrências por regra:")
        for code, qty in sorted(code_counts.items()):
            typer.echo(f"     • {code}: {qty}")

    if total_errors > 0 or (strict and total_warnings > 0):
        raise typer.Exit(code=1)


@app.command(name="validate-ids", rich_help_panel=_PANEL_VALIDATE)
def validate_ids(
    base_ref: str = typer.Option("HEAD", "--base-ref", help="Referência Git base para comparar invariantes do ledger."),
) -> None:
    """Valida imutabilidade e consistência de data/catalog-registry.json com os índices."""
    from scripts.indexer import validate_catalog_identities

    if not validate_catalog_identities(str(BASE_DIR), git_ref=base_ref):
        raise typer.Exit(code=1)


@app.command(name="validate-kindle", rich_help_panel=_PANEL_VALIDATE)
def validate_kindle_cmd(
    epub_file: str = typer.Argument(..., help="Caminho do arquivo EPUB para validação Amazon Kindle."),
    strict: bool = typer.Option(False, "--strict", help="Falha se houver avisos (warnings)."),
) -> None:
    """Valida a conformidade técnica e editorial de um EPUB para a Amazon (KDP / Send to Kindle)."""
    from scripts.kindle_validator import validate_kindle_epub

    typer.secho(f"🔍 Validando conformidade Amazon Kindle para '{epub_file}'...\n", fg=typer.colors.CYAN, bold=True)
    res = validate_kindle_epub(epub_file)

    if res.metadata:
        typer.secho("📋 Metadados Detectados:", fg=typer.colors.WHITE, bold=True)
        for k, v in res.metadata.items():
            typer.secho(f"   • {k}: {v}", fg=typer.colors.BLUE)

    if res.infos:
        typer.secho("\n✨ Conformidades Confirmadas:", fg=typer.colors.WHITE, bold=True)
        for info in res.infos:
            typer.secho(f"   ✓ {info}", fg=typer.colors.GREEN)

    if res.warnings:
        typer.secho(f"\n⚠️  Avisos e Recomendações ({len(res.warnings)}):", fg=typer.colors.YELLOW, bold=True)
        for warn in res.warnings:
            typer.secho(f"   ! {warn}", fg=typer.colors.YELLOW)

    if res.errors:
        typer.secho(f"\n❌ Erros Críticos de Conformidade KDP ({len(res.errors)}):", fg=typer.colors.RED, bold=True)
        for err in res.errors:
            typer.secho(f"   ✗ {err}", fg=typer.colors.RED)

    if not res.is_valid:
        typer.secho(
            "\n🚫 Validação Kindle: REPROVADO (o KDP poderá rejeitar ou apresentar erros neste arquivo).",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(code=1)

    if strict and res.warnings:
        typer.secho(
            "\n⚠️  Validação Kindle: APROVADO COM RESSALVAS (--strict ativo).", fg=typer.colors.YELLOW, bold=True
        )
        raise typer.Exit(code=1)

    typer.secho(
        "\n🎉 Validação Kindle: APROVADO! Arquivo 100% pronto para Amazon KDP / Send to Kindle.",
        fg=typer.colors.GREEN,
        bold=True,
    )


# ── 4. Publicação & Catálogo ───────────────────────────────────────────────────


@app.command(name="promote", rich_help_panel=_PANEL_PUBLISH)
def promote_cmd(
    review_file: str = typer.Argument(..., help="Caminho do arquivo em data/review/articles/ ou data/review/books/."),
    source: str | None = typer.Option(None, "--source", "-s", help="Matriz local original para auditoria final."),
    strict: bool = typer.Option(False, "--strict", help="Bloqueia promoção também em alertas (warnings)."),
    run_index: bool = typer.Option(
        False, "--index", help="Atualiza índices JSON e valida ledger de IDs após promover."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Executa o gate sem mover ou apagar arquivos."),
    translated: bool = typer.Option(False, "--translated", help="Usa faixas de comparação para obra traduzida."),
) -> None:
    """Valida e promove um documento de data/review/ para content/, limpando a cópia ativa."""
    from scripts.workflow import WorkflowError, promote_review

    try:
        res = promote_review(
            review_path=review_file,
            base_dir=BASE_DIR,
            source_path=source,
            strict=strict,
            run_index=run_index,
            dry_run=dry_run,
            translated=translated,
        )
        if res.dry_run:
            typer.secho(
                f"✅ [DRY-RUN] Gate aprovado. Destino seria: {res.content_path}",
                fg=typer.colors.CYAN,
            )
        else:
            typer.secho(f"✅ Obra promovida para: {res.content_path}", fg=typer.colors.GREEN)
            if res.removed_audit_path:
                typer.secho(f"🧹 Manifesto removido de review/: {res.removed_audit_path.name}", fg=typer.colors.BLUE)
    except (FileNotFoundError, WorkflowError) as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(rich_help_panel=_PANEL_PUBLISH)
def index() -> None:
    """Atualiza o JSON index de artigos, livros e periódicos."""
    update_index(str(BASE_DIR))


# ── 5. Capas & Mídia ───────────────────────────────────────────────────────────


@app.command(name="inject-text", rich_help_panel=_PANEL_COVERS)
@app.command(name="compose-cover", rich_help_panel=_PANEL_COVERS)
def inject_text(
    image_path: str = typer.Argument(..., help="Caminho da arte de fundo 2:3 sem texto."),
    slug: str | None = typer.Option(
        None, "--slug", "-s", help="Slug canônico da obra para localizar o YAML e nomear a capa."
    ),
    custom_text: str | None = typer.Option(
        None, "--custom-text", "-t", help="Texto manual no formato 'Título|Autor|Data'."
    ),
) -> None:
    """Compõe a tipografia editorial canônica sobre a arte de fundo e salva em assets/covers/<slug>.webp (WebP q100)."""
    from scripts.covers import inject_cover_text

    dest_path = inject_cover_text(str(BASE_DIR), image_path, custom_text=custom_text, target_slug=slug)
    if dest_path is None:
        raise typer.Exit(code=1)


# ── 6. Exportação & RAG ────────────────────────────────────────────────────────


@app.command(name="build-epub", rich_help_panel=_PANEL_EXPORT)
@app.command(name="epub", rich_help_panel=_PANEL_EXPORT)
def build_epub_cmd(
    input_file: str | None = typer.Argument(None, help="Caminho do arquivo Markdown (ou omitir com --all)."),
    output_file: str | None = typer.Option(None, "--output", "-o", help="Caminho do arquivo .epub de saída."),
    all_items: bool = typer.Option(False, "--all", "-a", help="Compila recursivamente todo o catálogo em lote."),
    target_type: str = typer.Option("all", "--type", "-t", help="Filtro para lote: 'all', 'books' ou 'articles'."),
    cover_file: str | None = typer.Option(None, "--cover", "-c", help="Caminho customizado da imagem de capa."),
    css_file: str | None = typer.Option(None, "--css", help="Folha de estilos customizada para o EPUB."),
    with_colophon: bool = typer.Option(False, "--colophon", help="Adiciona colofão editorial legado ao final."),
    no_institutional: bool = typer.Option(False, "--no-institutional", help="Desativa página institucional final."),
    flat: bool = typer.Option(False, "--flat", help="Salva diretamente na raiz de dist/ sem subpastas."),
) -> None:
    """Converte um ou todos os livros/artigos Markdown em EPUB 3 editorial com metadados e capa."""
    from scripts.md2epub import batch_convert_content, convert_md_to_epub

    if not all_items and not input_file:
        typer.secho(
            "❌ Forneça o caminho do arquivo Markdown ou utilize a flag '--all' para compilar em lote.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    try:
        if all_items:
            typer.secho(
                f"🚀 Iniciando compilação em lote do catálogo ({target_type})...\n", fg=typer.colors.CYAN, bold=True
            )
            res = batch_convert_content(
                base_dir=BASE_DIR,
                target_type=target_type,
                cover_path=cover_file,
                css_path=css_file,
                add_colophon=with_colophon,
                add_institutional_page=not no_institutional,
            )
            for item in res["succeeded"]:
                rel_out = (
                    item["output"].relative_to(BASE_DIR) if item["output"].is_relative_to(BASE_DIR) else item["output"]
                )
                typer.secho(f"  ✅ {item['source'].stem} -> {rel_out} ({item['size_kb']} KB)", fg=typer.colors.GREEN)

            if res["failed"]:
                typer.secho(f"\n⚠️  {len(res['failed'])} arquivo(s) com erro:", fg=typer.colors.YELLOW, bold=True)
                for failed in res["failed"]:
                    typer.secho(f"  ❌ {failed['source']}: {failed['error']}", fg=typer.colors.RED)

            typer.secho(
                f"\n🎉 Concluído: {len(res['succeeded'])}/{res['total']} documentos gerados com sucesso!",
                fg=typer.colors.GREEN,
                bold=True,
            )
            if res["failed"]:
                raise typer.Exit(code=1)
            return

        assert input_file is not None
        typer.secho(f"📖 Convertendo '{input_file}' para EPUB 3...", fg=typer.colors.CYAN)
        out_path = convert_md_to_epub(
            input_md_path=input_file,
            output_epub_path=output_file,
            cover_path=cover_file,
            css_path=css_file,
            base_dir=BASE_DIR,
            add_colophon=with_colophon,
            add_institutional_page=not no_institutional,
            structured=not flat,
        )
        size_kb = round(out_path.stat().st_size / 1024, 1)
        typer.secho("✅ EPUB gerado com sucesso!", fg=typer.colors.GREEN, bold=True)
        typer.secho(f"   📁 Arquivo: {out_path} ({size_kb} KB)", fg=typer.colors.WHITE)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.secho(f"❌ Erro ao gerar EPUB: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="build-print", rich_help_panel=_PANEL_EXPORT)
@app.command(name="print", rich_help_panel=_PANEL_EXPORT)
def build_print_cmd(
    input_file: str | None = typer.Argument(None, help="Caminho do arquivo Markdown (ou omitir com --all)."),
    all_items: bool = typer.Option(False, "--all", "-a", help="Compila em lote todos os livros de content/books."),
    trim_size: str = typer.Option("14x21", "--trim-size", "-t", help="Dimensão do miolo: '14x21' ou '6x9'."),
    paper_type: str = typer.Option("cream", "--paper", "-p", help="Tipo de papel para lombada: 'cream' ou 'white'."),
) -> None:
    """Compila livro impresso sob demanda para Amazon KDP (Miolo 14x21cm + Capa aberta c/ lombada calculada)."""
    from scripts.md2print import batch_convert_print, convert_md_to_print

    if not all_items and not input_file:
        typer.secho(
            "❌ Forneça o arquivo Markdown do livro ou use a flag '--all' para compilar em lote.", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    try:
        if all_items:
            typer.secho(
                "🚀 Iniciando compilação de livros físicos em lote para impressão...\n", fg=typer.colors.CYAN, bold=True
            )
            res_batch = batch_convert_print(base_dir=BASE_DIR)
            for item in res_batch["succeeded"]:
                rel_src = item["source"].name
                typer.secho(
                    f"  ✅ {rel_src}: {item['pages']} págs | Lombada: {item['spine_mm']} mm", fg=typer.colors.GREEN
                )
                typer.secho(f"     📖 Miolo: {item['interior_pdf']}", fg=typer.colors.WHITE)
                typer.secho(f"     🎨 Capa:  {item['cover_pdf']}\n", fg=typer.colors.WHITE)

            if res_batch["failed"]:
                typer.secho(f"⚠️  {len(res_batch['failed'])} arquivo(s) com erro:", fg=typer.colors.YELLOW, bold=True)
                for failed in res_batch["failed"]:
                    typer.secho(f"  ❌ {failed['source']}: {failed['error']}", fg=typer.colors.RED)

            typer.secho(
                f"🎉 Concluído: {len(res_batch['succeeded'])}/{res_batch['total']} livros gerados para impressão!",
                fg=typer.colors.GREEN,
                bold=True,
            )
            if res_batch["failed"]:
                raise typer.Exit(code=1)
            return

        assert input_file is not None
        typer.secho(f"📖 Compilando livro físico para impressão a partir de '{input_file}'...", fg=typer.colors.CYAN)
        res = convert_md_to_print(
            input_md_path=input_file,
            base_dir=BASE_DIR,
            trim_size=trim_size,
            paper_type=paper_type,
        )

        typer.secho("\n✅ Livro Físico gerado com sucesso!", fg=typer.colors.GREEN, bold=True)
        typer.secho(f"   📄 Miolo (14x21 cm):  {res['interior_pdf']}", fg=typer.colors.WHITE)
        typer.secho(f"      • Páginas: {res['pages']} | Tamanho: {res['interior_size_kb']} KB", fg=typer.colors.BLUE)
        typer.secho(f"   🎨 Capa Aberta KDP:   {res['cover_pdf']}", fg=typer.colors.WHITE)
        typer.secho(f"      • Lombada: {res['spine_mm']} mm | Tamanho: {res['cover_size_kb']} KB", fg=typer.colors.BLUE)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.secho(f"❌ Erro ao compilar livro impresso: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="export-pdf", rich_help_panel=_PANEL_EXPORT)
def export_pdf_cmd(
    input_file: str = typer.Argument(..., help="Caminho do arquivo Markdown para conversão."),
    output_file: str | None = typer.Option(None, "--output", "-o", help="Caminho do PDF de saída (opcional)."),
) -> None:
    """Converte um documento Markdown para PDF com design editorial elegante e paleta LeiaME."""
    try:
        from scripts.md2pdf import convert_md_to_pdf

        in_path = Path(input_file)
        out_path = in_path.with_suffix(".pdf") if not output_file else Path(output_file)
        convert_md_to_pdf(str(in_path), str(out_path))
        typer.secho(f"✅ PDF gerado com sucesso: {out_path}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"❌ Erro ao exportar PDF: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="build-rag", rich_help_panel=_PANEL_EXPORT)
def build_rag_cmd(
    output: str | None = typer.Option(None, "--output", "-o", help="Caminho personalizado para o banco SQLite."),
) -> None:
    """Compila o banco de dados SQLite RAG local com FTS5 a partir dos artigos e livros."""
    try:
        from scripts.rag import build_rag_database

        typer.secho("⚡ Compilando banco de dados SQLite RAG...", fg=typer.colors.CYAN)
        db_file = build_rag_database(BASE_DIR, output_path=output)
        size_kb = round(db_file.stat().st_size / 1024, 1)
        typer.secho("✅ Banco SQLite RAG compilado com sucesso!", fg=typer.colors.GREEN, bold=True)
        typer.secho(f"   📁 Arquivo: {db_file} ({size_kb} KB)", fg=typer.colors.WHITE)
    except Exception as exc:
        typer.secho(f"❌ Erro ao compilar banco RAG: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command(name="search-rag", rich_help_panel=_PANEL_EXPORT)
def search_rag_cmd(
    query: str = typer.Argument(..., help="Termo de busca ou pergunta para o motor RAG."),
    limit: int = typer.Option(5, "--limit", "-l", help="Quantidade máxima de trechos a retornar."),
    doc_type: str | None = typer.Option(None, "--type", "-t", help="Filtrar por tipo: 'article' ou 'book'."),
    ai_format: bool = typer.Option(False, "--ai", help="Exibir no formato pronto para prompt de IA/LLM."),
    db_path: str | None = typer.Option(None, "--db", help="Caminho personalizado do banco SQLite."),
) -> None:
    """Executa busca semântico-textual BM25 com snippets e caminhos dos arquivos físicos."""
    try:
        from scripts.rag import format_ai_prompt_context, search_rag

        target_db = Path(db_path) if db_path else BASE_DIR / "data" / "openscimd_rag.sqlite"
        results = search_rag(query, db_path=target_db, limit=limit, doc_type=doc_type)

        if not results:
            typer.secho(f"🔍 Nenhum resultado encontrado para: '{query}'", fg=typer.colors.YELLOW)
            return

        if ai_format:
            typer.echo(format_ai_prompt_context(results))
            return

        typer.secho(f"\n🔍 {len(results)} trecho(s) encontrado(s) para '{query}':\n", fg=typer.colors.GREEN, bold=True)
        for idx, res_item in enumerate(results, start=1):
            typer.secho(
                f"[{idx}] {res_item['doc_title']} — {res_item['doc_author']} ({res_item['doc_type'].upper()})",
                fg=typer.colors.CYAN,
                bold=True,
            )
            typer.secho(
                f"    📖 Seção: {res_item['heading']} | Score BM25: {res_item['rank_score']}", fg=typer.colors.WHITE
            )
            typer.secho(f"    📄 Markdown: {res_item['markdown_path']}", fg=typer.colors.MAGENTA)
            if res_item["source_path"]:
                typer.secho(f"    🔗 Fonte Primária: {res_item['source_path']}", fg=typer.colors.BLUE)
            typer.secho(f"    📝 Trecho: {res_item['highlighted_snippet']}\n", fg=typer.colors.YELLOW)
    except Exception as exc:
        typer.secho(f"❌ Erro na busca RAG: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


# ── 7. Tradução (Experimental / Em Redesign) ──────────────────────────────────


@app.command(rich_help_panel=_PANEL_TRANSLATE)
def check_translation(
    english_file: str = typer.Argument(..., help="Arquivo de texto original em Inglês."),
    pt_file: str | None = typer.Argument(None, help="Arquivo opcional com a tradução em PT para avaliar."),
) -> None:
    """[Experimental] Avalia a fidelidade semântica de uma tradução usando MarianMT e Back-Translation."""
    from scripts.fidelity_checker import test_fidelity

    with open(english_file, encoding="utf-8") as f:
        en_text = f.read().strip()

    pt_text: str | None = None
    if pt_file and os.path.exists(pt_file):
        with open(pt_file, encoding="utf-8") as f:
            pt_text = f.read().strip()

    test_fidelity(en_text, pt_text)


@app.command(rich_help_panel=_PANEL_TRANSLATE)
def pipeline_review(
    raw_en_file: str = typer.Argument(..., help="Arquivo Inglês original."),
    pt_file: str = typer.Argument(..., help="Arquivo PT traduzido."),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Limite de linhas ou parágrafos para testes."),
    start: int | None = typer.Option(None, "--start", "-s", help="Índice do bloco inicial (1-based)."),
    end: int | None = typer.Option(None, "--end", "-e", help="Índice do bloco final (1-based)."),
) -> None:
    """[Experimental] Gera relatório de fidelidade extraindo blocos de texto puro."""
    from scripts.alignment_pipeline import run_alignment_and_report

    run_alignment_and_report(raw_en_file, pt_file, limit=limit, start=start, end=end)


@app.command(rich_help_panel=_PANEL_TRANSLATE)
def translate_file(
    input_file: str = typer.Argument(..., help="Arquivo em Inglês para traduzir."),
    output_file: str = typer.Argument(..., help="Caminho para salvar a tradução em PT."),
) -> None:
    """[Experimental] Traduz um documento do Inglês para o Português linha a linha usando MarianMT."""
    from tqdm import tqdm

    from scripts.fidelity_checker import get_models, translate

    print("Carregando modelos MarianMT...")
    tokenizer_en_pt, model_en_pt, _, _ = get_models()

    with open(input_file, encoding="utf-8") as f:
        lines = f.readlines()

    translated_lines: list[str] = []
    for line in tqdm(lines, desc="Traduzindo documento"):
        stripped = line.strip()
        if not stripped or stripped == "---" or stripped.startswith("title:") or stripped.startswith("author:"):
            translated_lines.append(line)
            continue

        pt_text = translate(stripped, tokenizer_en_pt, model_en_pt)
        translated_lines.append(line.replace(stripped, pt_text))

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(translated_lines)


if __name__ == "__main__":
    app()
