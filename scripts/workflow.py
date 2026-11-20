"""Fluxo de trabalho editorial: abertura de revisão (start-review) e promoção (promote)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scripts.indexer import update_index, validate_catalog_identities
from scripts.validator import (
    FileValidationResult,
    print_file_validation_result,
    validate_single_file,
)

ReviewDocType = Literal["articles", "books"]


class WorkflowError(RuntimeError):
    """Erro operacional no fluxo editorial entre raw/draft, review e content."""


@dataclass(frozen=True)
class StartReviewResult:
    """Resultado da preparação de um documento na mesa ativa data/review/."""

    source_path: Path
    review_path: Path
    audit_path: Path | None
    doc_type: ReviewDocType
    total_lines: int
    block_count: int


@dataclass(frozen=True)
class PromoteResult:
    """Resultado da promoção de um documento validado de data/review/ para content/."""

    review_path: Path
    content_path: Path
    removed_audit_path: Path | None
    validation: FileValidationResult
    indexed: bool
    dry_run: bool


def _resolve_input_path(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.resolve()
    rel_to_root = (root / candidate).resolve()
    if rel_to_root.exists():
        return rel_to_root
    return candidate.resolve()


def _build_audit_manifest(
    source_path: Path,
    review_path: Path,
    root: Path,
    total_lines: int,
    block_size: int = 200,
) -> tuple[str, int]:
    try:
        src_display = source_path.relative_to(root).as_posix()
    except ValueError:
        src_display = str(source_path)

    try:
        rev_display = review_path.relative_to(root).as_posix()
    except ValueError:
        rev_display = str(review_path)

    block_lines: list[str] = []
    block_idx = 0
    for start in range(1, max(1, total_lines) + 1, block_size):
        block_idx += 1
        end = min(total_lines, start + block_size - 1)
        block_lines.append(
            f"- [ ] **Bloco {block_idx}** (`L{start}–L{end}`) — Seções: `_` | Notas: `_` | Observações: `_`"
        )

    content = (
        f"# Manifesto de Auditoria Linha a Linha — {review_path.stem}\n\n"
        f"- **Origem**: `{src_display}`\n"
        f"- **Arquivo em Revisão**: `{rev_display}`\n"
        f"- **Total de Linhas**: {total_lines}\n"
        f"- **Tamanho de Bloco**: {block_size} linhas\n\n"
        "---\n\n"
        "## Cobertura por Blocos\n\n"
        + "\n".join(block_lines)
        + "\n\n---\n\n"
        "## Definition of Done (DoD)\n\n"
        f"- [ ] Todos os {block_idx} bloco(s) lidos integralmente e confrontados contra a matriz local\n"
        f"- [ ] `uv run openscimd review --check \"{rev_display}\"` inspecionado\n"
        f"- [ ] `uv run openscimd validate --file \"{rev_display}\"` aprovado com 0 erros\n"
        f"- [ ] Autorização explícita para `uv run openscimd promote \"{rev_display}\" --index`\n"
    )
    return content, block_idx


def start_review(
    source_path: str | Path,
    base_dir: str | Path,
    dest_rel: str | Path | None = None,
    doc_type: ReviewDocType | None = None,
    create_audit: bool = True,
    overwrite: bool = False,
    block_size: int = 200,
) -> StartReviewResult:
    """Copia um rascunho ou obra já publicada para edição ativa em data/review/."""
    root = Path(base_dir).resolve()
    src = _resolve_input_path(source_path, root)

    if not src.is_file():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {src}")
    if src.name.endswith(".audit.md"):
        raise WorkflowError("Arquivos '.audit.md' são manifestos de auditoria e não entram em revisão.")

    review_root = (root / "data" / "review").resolve()
    if src.is_relative_to(review_root):
        raise WorkflowError(f"O arquivo já reside na mesa de revisão ativa: {src}")

    content_articles = (root / "content" / "articles").resolve()
    content_books = (root / "content" / "books").resolve()
    draft_root = (root / "data" / "draft").resolve()

    resolved_type: ReviewDocType
    default_rel: Path

    if src.is_relative_to(content_articles):
        resolved_type = "articles"
        default_rel = src.relative_to(content_articles)
    elif src.is_relative_to(content_books):
        resolved_type = "books"
        default_rel = src.relative_to(content_books)
    else:
        raw_dest = Path(dest_rel) if dest_rel is not None else None
        if raw_dest is not None and raw_dest.parts and raw_dest.parts[0] in ("articles", "books"):
            prefix_type: ReviewDocType = "articles" if raw_dest.parts[0] == "articles" else "books"
            if doc_type is not None and doc_type != prefix_type:
                raise WorkflowError(
                    f"Conflito entre --type '{doc_type}' e prefixo de --dest '{raw_dest.parts[0]}/'."
                )
            resolved_type = prefix_type
            raw_dest = Path(*raw_dest.parts[1:]) if len(raw_dest.parts) > 1 else Path(src.name)
            dest_rel = raw_dest
        elif doc_type is not None:
            resolved_type = doc_type
        else:
            raise WorkflowError(
                "Para iniciar revisão de arquivo fora de content/, informe '--type articles' ou '--type books'."
            )

        if src.is_relative_to(draft_root):
            rel_in_draft = src.relative_to(draft_root)
            if rel_in_draft.parts and rel_in_draft.parts[0] in ("articles", "books"):
                rel_in_draft = (
                    Path(*rel_in_draft.parts[1:]) if len(rel_in_draft.parts) > 1 else Path(src.name)
                )
            default_rel = rel_in_draft
        else:
            default_rel = Path(src.name)

    target_rel = Path(dest_rel) if dest_rel is not None else default_rel
    if target_rel.suffix.lower() != ".md":
        target_rel = target_rel.with_suffix(".md")

    type_review_root = (review_root / resolved_type).resolve()
    review_dest = (type_review_root / target_rel).resolve()

    if not review_dest.is_relative_to(type_review_root):
        raise WorkflowError(f"Caminho de destino inválido fora de data/review/{resolved_type}: {target_rel}")

    if review_dest.exists() and not overwrite:
        raise FileExistsError(
            f"Arquivo já está em revisão ativa: {review_dest}. Use --overwrite para sobrescrever."
        )

    review_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, review_dest)

    lines = review_dest.read_text(encoding="utf-8").splitlines()
    total_lines = max(1, len(lines))

    audit_path: Path | None = None
    block_count = (total_lines + block_size - 1) // block_size
    if create_audit:
        audit_path = review_dest.with_suffix(".audit.md")
        manifest_text, block_count = _build_audit_manifest(
            source_path=src,
            review_path=review_dest,
            root=root,
            total_lines=total_lines,
            block_size=block_size,
        )
        audit_path.write_text(manifest_text, encoding="utf-8")

    return StartReviewResult(
        source_path=src,
        review_path=review_dest,
        audit_path=audit_path,
        doc_type=resolved_type,
        total_lines=total_lines,
        block_count=block_count,
    )


def _prune_empty_review_dirs(start_dir: Path, stop_root: Path) -> None:
    current = start_dir.resolve()
    stop = stop_root.resolve()
    while current != stop and current.is_relative_to(stop):
        if any(current.iterdir()):
            break
        current.rmdir()
        current = current.parent


def promote_review(
    review_path: str | Path,
    base_dir: str | Path,
    source_path: str | Path | None = None,
    strict: bool = False,
    run_index: bool = False,
    dry_run: bool = False,
    translated: bool = False,
) -> PromoteResult:
    """Valida e promove documento de data/review/ para content/, limpando a cópia ativa."""
    root = Path(base_dir).resolve()
    rev = _resolve_input_path(review_path, root)

    if not rev.is_file():
        raise FileNotFoundError(f"Arquivo em revisão não encontrado: {rev}")
    if rev.name.endswith(".audit.md"):
        raise WorkflowError("Não é possível promover um manifesto '.audit.md'. Informe o arquivo '.md' da obra.")

    review_articles = (root / "data" / "review" / "articles").resolve()
    review_books = (root / "data" / "review" / "books").resolve()

    if rev.is_relative_to(review_articles):
        rel = rev.relative_to(review_articles)
        content_dest = (root / "content" / "articles" / rel).resolve()
        stop_dir = review_articles
        resolved_doc_type: Literal["article", "book"] = "article"
    elif rev.is_relative_to(review_books):
        rel = rev.relative_to(review_books)
        content_dest = (root / "content" / "books" / rel).resolve()
        stop_dir = review_books
        resolved_doc_type = "book"
    else:
        raise WorkflowError(
            "O arquivo a promover deve residir em 'data/review/articles/' ou 'data/review/books/'."
        )

    resolved_source = _resolve_input_path(source_path, root) if source_path is not None else None

    validation = validate_single_file(
        rev,
        base_dir=root,
        doc_type=resolved_doc_type,
        check_editorial=True,
        check_assets=False,
        source_path=resolved_source,
        translated=translated,
        strict_language=True,
    )
    print_file_validation_result(validation, label=rel.as_posix())

    if not validation.is_valid(strict=strict):
        raise WorkflowError(
            f"Promoção bloqueada: '{rev.name}' possui {validation.total_errors} erro(s) "
            f"e {validation.total_warnings} alerta(s)."
        )

    audit_path = rev.with_suffix(".audit.md")
    removed_audit: Path | None = None

    if dry_run:
        return PromoteResult(
            review_path=rev,
            content_path=content_dest,
            removed_audit_path=audit_path if audit_path.exists() else None,
            validation=validation,
            indexed=False,
            dry_run=True,
        )

    content_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rev, content_dest)
    rev.unlink()
    if audit_path.exists():
        audit_path.unlink()
        removed_audit = audit_path

    _prune_empty_review_dirs(rev.parent, stop_dir)

    indexed = False
    if run_index:
        update_index(str(root))
        if (root / "index-articles.json").exists() and (root / "index-books.json").exists():
            if not validate_catalog_identities(str(root), git_ref="HEAD"):
                raise WorkflowError("Falha na verificação de invariantes de IDs (validate-ids) após indexação.")
        indexed = True

    return PromoteResult(
        review_path=rev,
        content_path=content_dest,
        removed_audit_path=removed_audit,
        validation=validation,
        indexed=indexed,
        dry_run=False,
    )
