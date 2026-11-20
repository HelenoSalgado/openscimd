"""Validadores determinísticos de metadados YAML e integridade editorial."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from scripts.categories import validate_categories
from scripts.editorial_linter import (
    EditorialIssue,
    LintReport,
    SourceComparisonReport,
    lint_markdown_file,
)
from scripts.utils import get_files_recursively, parse_date_to_timestamp, parse_markdown_file

DocType = Literal["article", "book"]
ALLOWED_LANGUAGES: frozenset[str] = frozenset({"pt-BR", "pt-PT"})
_PLACEHOLDER_TITLES: frozenset[str] = frozenset({"sem título", "sem titulo", "título", "untitled"})
_PLACEHOLDER_AUTHORS: frozenset[str] = frozenset({"desconhecido", "unknown", "autor desconhecido"})


@dataclass(frozen=True)
class FileValidationResult:
    """Resultado consolidado da validação de metadados e linter editorial de um documento."""

    file_path: Path
    doc_type: DocType
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    editorial_issues: list[EditorialIssue] = field(default_factory=list)
    source_comparison: SourceComparisonReport | None = None

    @property
    def all_editorial_issues(self) -> list[EditorialIssue]:
        if self.source_comparison is None:
            return list(self.editorial_issues)
        return [*self.editorial_issues, *self.source_comparison.issues]

    @property
    def total_errors(self) -> int:
        ed_errors = sum(1 for issue in self.all_editorial_issues if issue.severity == "error")
        return len(self.errors) + ed_errors

    @property
    def total_warnings(self) -> int:
        ed_warnings = sum(1 for issue in self.all_editorial_issues if issue.severity == "warning")
        return len(self.warnings) + ed_warnings

    def is_valid(self, strict: bool = False) -> bool:
        if self.total_errors > 0:
            return False
        if strict and self.total_warnings > 0:
            return False
        return True


def infer_doc_type(file_path: Path, metadata: dict[str, Any] | None = None) -> DocType:
    """Infere se o documento é 'article' ou 'book' a partir do caminho ou do YAML."""
    parts = {part.lower() for part in file_path.parts}
    if "articles" in parts:
        return "article"
    if "books" in parts:
        return "book"
    meta = metadata or {}
    if any(key in meta for key in ("pages", "journal", "e_issn", "keywords")):
        return "article"
    return "book"


def _validate_metadata_common(
    metadata: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    strict_language: bool,
) -> None:
    title = metadata.get("title")
    if not title or not str(title).strip():
        errors.append('Campo obrigatório "title" está ausente ou vazio.')
    elif str(title).strip().lower() in _PLACEHOLDER_TITLES:
        errors.append(f'Campo "title" contém placeholder inválido ("{title}").')

    has_author = bool(
        metadata.get("author")
        and str(metadata.get("author")).strip()
        and str(metadata.get("author")).strip().lower() not in _PLACEHOLDER_AUTHORS
    )
    raw_authors = metadata.get("authors")
    has_authors = bool(raw_authors and isinstance(raw_authors, list) and raw_authors)
    if not has_author and not has_authors:
        if metadata.get("author") and str(metadata.get("author")).strip().lower() in _PLACEHOLDER_AUTHORS:
            errors.append(f'Campo "author" contém placeholder inválido ("{metadata.get("author")}").')
        else:
            errors.append('Campo de autoria obrigatório ("author" ou "authors") ausente ou vazio.')

    summary = metadata.get("summary") or metadata.get("sumary")
    if not summary or not str(summary).strip():
        errors.append('Resumo ("summary" ou "sumary") ausente ou vazio.')
    elif metadata.get("sumary"):
        warnings.append('Encontrado erro de digitação no campo "sumary". Recomenda-se renomear para "summary".')

    license_ = metadata.get("license") or metadata.get("licence")
    if not license_ or not str(license_).strip():
        errors.append('Campo de licença obrigatório ("license" ou "licence") ausente ou vazio.')
    elif metadata.get("licence"):
        warnings.append('Chave de licença escrita como "licence". Recomenda-se padronizar para "license".')

    if "category" in metadata and "categories" not in metadata:
        warnings.append('Uso da chave obsoleta "category". Padronize para "categories".')
        raw_cat = metadata.get("category")
        cat_val = [raw_cat] if isinstance(raw_cat, str) else raw_cat
    else:
        cat_val = metadata.get("categories")

    errors.extend(validate_categories(cat_val))

    lang = metadata.get("language")
    if not lang or str(lang).strip() not in ALLOWED_LANGUAGES:
        msg = (
            f'Campo "language" ausente ou fora do padrão ("{lang}"). '
            'Use "pt-BR" ou "pt-PT".'
        )
        if strict_language:
            errors.append(msg)
        else:
            warnings.append(msg)


def validate_single_file(
    file_path: str | Path,
    base_dir: str | Path,
    doc_type: DocType | None = None,
    check_editorial: bool = True,
    check_assets: bool = False,
    source_path: str | Path | None = None,
    translated: bool = False,
    strict_language: bool = True,
) -> FileValidationResult:
    """Valida metadados YAML e (opcionalmente) regras editoriais e matriz-fonte de um único arquivo."""
    target = Path(file_path)
    root = Path(base_dir)
    errors: list[str] = []
    warnings: list[str] = []
    editorial_issues: list[EditorialIssue] = []
    comparison: SourceComparisonReport | None = None

    try:
        content = target.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append('O arquivo não inicia com delimitadores de metadados ("---").')

        parsed = parse_markdown_file(str(target))
        metadata: dict[str, Any] = parsed["metadata"]
        resolved_type: DocType = doc_type or infer_doc_type(target, metadata)

        _validate_metadata_common(metadata, errors, warnings, strict_language=strict_language)

        if resolved_type == "article":
            if not metadata.get("date"):
                errors.append('Campo obrigatório "date" ausente.')
            elif not parse_date_to_timestamp(metadata.get("date")):
                errors.append(
                    f'Formato de data inválido: "{metadata.get("date")}". '
                    "Use YYYY-MM-DD, DD-MM-YYYY ou padrão ABNT brasileiro (ex.: 20 nov. 2025)."
                )

            pages = metadata.get("pages")
            if not pages or not str(pages).strip():
                errors.append('Campo obrigatório "pages" está ausente ou vazio.')

            m_vol = re.search(r"vol-(\d+)", target.as_posix())
            if m_vol:
                expected_vol = m_vol.group(1)
                actual_vol = metadata.get("volume")
                if actual_vol is None:
                    errors.append(
                        f'Artigo reside na pasta "vol-{expected_vol}", mas o campo obrigatório "volume" está ausente no YAML.'
                    )
                elif str(actual_vol) != expected_vol:
                    errors.append(
                        f'Divergência de Volume: YAML declara volume "{actual_vol}", '
                        f'mas o arquivo reside na pasta "vol-{expected_vol}".'
                    )

            if not metadata.get("doi") and not metadata.get("DOI"):
                warnings.append('Campo recomendado "DOI" está ausente.')
            if not metadata.get("journal"):
                warnings.append('Campo administrativo "journal" está ausente.')

            if check_assets:
                base_name = target.stem
                if not (root / "assets" / "covers" / "mobile" / f"{base_name}.webp").exists():
                    warnings.append(
                        f"Imagem de capa mobile correspondente não localizada em assets/covers/mobile/{base_name}.webp."
                    )
                sources_dir = root / "assets" / "sources"
                if not (sources_dir / f"{base_name}.pdf").exists() and not any(sources_dir.glob(f"{base_name}.*")):
                    warnings.append(f"Arquivo de fonte original não localizado em assets/sources/{base_name}.*")

        else:
            if not metadata.get("date"):
                errors.append('Campo obrigatório "date" ausente.')

            if "keywords" in metadata:
                errors.append(
                    'E-books não possuem o campo "keywords". Palavras-chave são exclusivas para artigos acadêmicos.'
                )

            if check_assets:
                base_name = target.stem
                if not (root / "assets" / "covers" / "mobile" / f"{base_name}.webp").exists():
                    warnings.append(
                        f"Imagem de capa mobile correspondente não localizada em assets/covers/mobile/{base_name}.webp."
                    )

        if check_editorial:
            lint_report: LintReport = lint_markdown_file(
                target,
                source_path=source_path,
                translated=translated,
            )
            editorial_issues = lint_report.issues
            comparison = lint_report.comparison

    except Exception as e:
        resolved_type = doc_type or infer_doc_type(target)
        errors.append(f"Falha crítica ao ler/processar arquivo: {e}")

    return FileValidationResult(
        file_path=target,
        doc_type=resolved_type,
        errors=errors,
        warnings=warnings,
        editorial_issues=editorial_issues,
        source_comparison=comparison,
    )


def print_file_validation_result(result: FileValidationResult, label: str | None = None) -> None:
    """Imprime relatório legível dos erros e alertas de um FileValidationResult."""
    if result.total_errors == 0 and result.total_warnings == 0:
        return

    icon = "📄 Artigo" if result.doc_type == "article" else "📚 E-book"
    print(f"{icon}: {label or result.file_path}")
    for err in result.errors:
        print(f"  ❌ [ERRO] {err}")
    for warn in result.warnings:
        print(f"  ⚠️ [ALERTA] {warn}")
    for issue in result.all_editorial_issues:
        line_tag = f"L{issue.line}" if issue.line is not None else "Geral"
        prefix = "❌ [ERRO" if issue.severity == "error" else "⚠️ [ALERTA"
        print(f"  {prefix} {issue.code} @ {line_tag}] {issue.message}")
    print("")


def validate_articles(
    base_dir: str,
    check_editorial: bool = False,
    strict: bool = False,
) -> bool:
    """Valida formato, metadados e categorias dos artigos acadêmicos em content/articles."""
    print("🧪 Iniciando validação de formato e metadados dos artigos...\n")
    articles_dir = Path(base_dir) / "content" / "articles"

    if not articles_dir.exists():
        print(f"❌ Diretório de artigos não encontrado em: {articles_dir}")
        return False

    invalid_count = 0
    total_errors = 0
    total_warnings = 0

    files = [Path(p) for p in get_files_recursively(articles_dir)]
    for file in files:
        rel_path = file.relative_to(articles_dir).as_posix()
        res = validate_single_file(
            file,
            base_dir=base_dir,
            doc_type="article",
            check_editorial=check_editorial,
            check_assets=True,
            strict_language=False,
        )
        # No modo global legado (sem check_editorial), suprime alerta de language para manter saída limpa até saneamento
        if not check_editorial:
            filtered_warnings = [w for w in res.warnings if not w.startswith('Campo "language"')]
            res = FileValidationResult(
                file_path=res.file_path,
                doc_type=res.doc_type,
                errors=res.errors,
                warnings=filtered_warnings,
                editorial_issues=res.editorial_issues,
                source_comparison=res.source_comparison,
            )

        if not res.is_valid(strict=strict):
            invalid_count += 1
        total_errors += res.total_errors
        total_warnings += res.total_warnings
        print_file_validation_result(res, label=rel_path)

    print("-" * 50)
    print("📊 Resumo da Validação de Artigos:")
    print(f"   - Artigos Verificados: {len(files)}")
    print(f"   - Artigos com Erros Fatais: {invalid_count}")
    print(f"   - Total de Erros: {total_errors}")
    print(f"   - Total de Alertas: {total_warnings}\n")

    if invalid_count > 0:
        print("❌ Falha na validação de artigos! Corrija os erros listados.")
        return False
    print("✅ Validação de artigos concluída com sucesso! Todos os artigos estão aptos.")
    return True


def validate_books(
    base_dir: str,
    check_editorial: bool = False,
    strict: bool = False,
) -> bool:
    """Valida formato, metadados e categorias dos e-books e volumes em content/books."""
    print("📚 Iniciando validação de formato e metadados dos e-books...\n")
    books_dir = Path(base_dir) / "content" / "books"

    if not books_dir.exists():
        print(f"❌ Diretório de livros não encontrado em: {books_dir}")
        return False

    invalid_count = 0
    total_errors = 0
    total_warnings = 0

    files = [Path(p) for p in get_files_recursively(books_dir)]
    for file in files:
        rel_path = file.relative_to(books_dir).as_posix()
        res = validate_single_file(
            file,
            base_dir=base_dir,
            doc_type="book",
            check_editorial=check_editorial,
            check_assets=True,
            strict_language=False,
        )
        if not check_editorial:
            filtered_warnings = [w for w in res.warnings if not w.startswith('Campo "language"')]
            res = FileValidationResult(
                file_path=res.file_path,
                doc_type=res.doc_type,
                errors=res.errors,
                warnings=filtered_warnings,
                editorial_issues=res.editorial_issues,
                source_comparison=res.source_comparison,
            )

        if not res.is_valid(strict=strict):
            invalid_count += 1
        total_errors += res.total_errors
        total_warnings += res.total_warnings
        print_file_validation_result(res, label=rel_path)

    print("-" * 50)
    print("📊 Resumo da Validação de E-books:")
    print(f"   - Livros Verificados: {len(files)}")
    print(f"   - Livros com Erros Fatais: {invalid_count}")
    print(f"   - Total de Erros: {total_errors}")
    print(f"   - Total de Alertas: {total_warnings}\n")

    if invalid_count > 0:
        print("❌ Falha na validação de e-books! Corrija os erros listados.")
        return False
    print("✅ Validação de e-books concluída com sucesso! Todos os e-books estão aptos.")
    return True


def validate_all(
    base_dir: str,
    check_editorial: bool = False,
    strict: bool = False,
) -> bool:
    """Valida artigos e e-books."""
    articles_ok = validate_articles(base_dir, check_editorial=check_editorial, strict=strict)
    print("\n" + "=" * 50 + "\n")
    books_ok = validate_books(base_dir, check_editorial=check_editorial, strict=strict)
    return articles_ok and books_ok
