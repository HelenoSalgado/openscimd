"""OpenSciMD Spellchecker and Archaic Orthography Review System."""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Iterable, List, Optional

from scripts.spellchecker.dictionary import DictionaryManager
from scripts.spellchecker.engine import ReviewEngine
from scripts.spellchecker.hunspell_client import HunspellClient
from scripts.spellchecker.masker import MarkdownMasker
from scripts.spellchecker.matcher import ArchaicMatcher, CasePreserver
from scripts.spellchecker.models import FileReviewResult, ReviewAction, ReviewMatch, ReviewSummary
from scripts.spellchecker.ui import Colors, InteractiveReviewUI


def review_path(
    path: Path | str,
    output_path: Optional[Path | str] = None,
    dict_path: Optional[Path | str] = None,
    auto_apply: bool = False,
    dry_run: bool = False,
    backup: bool = False,
    use_hunspell: bool = True,
) -> ReviewSummary:
    """
    Reviews a file or directory of markdown files for archaic orthography and spelling.
    If output_path is provided for a single file, writes reviewed content to output_path
    and preserves original file intact.
    """
    p = Path(path)
    custom_dicts = [dict_path] if dict_path else None
    dict_manager = DictionaryManager(custom_dict_paths=custom_dicts)
    hunspell_client = HunspellClient() if use_hunspell else None
    engine = ReviewEngine(dict_manager=dict_manager, hunspell_client=hunspell_client, use_hunspell=use_hunspell)
    ui = InteractiveReviewUI(engine=engine)

    target_files: List[Path] = []
    if p.is_file():
        target_files.append(p)
    elif p.is_dir():
        target_files.extend(sorted(p.rglob("*.md")))
    else:
        # Glob pattern support
        matches = glob.glob(str(path), recursive=True)
        target_files.extend(sorted([Path(m) for m in matches if Path(m).is_file() and m.endswith(".md")]))

    summary = ReviewSummary(files_processed=len(target_files))

    if not target_files:
        print(f"{Colors.YELLOW}Nenhum arquivo markdown encontrado para: {path}{Colors.ENDC}")
        return summary

    for target_file in target_files:
        # Output destination for this file
        dest_file = Path(output_path) if output_path and len(target_files) == 1 else None

        if dry_run:
            res = engine.dry_run_file(target_file)
            print(f"[{'⚠️ ' if res.total_found > 0 else '✅'}] {target_file}: {res.total_found} arcaísmos/erros encontrados.")
        elif auto_apply:
            res = engine.auto_apply_file(target_file, output_path=dest_file, create_backup=backup)
            if res.modified:
                out_name = res.output_filepath.name if res.output_filepath else target_file.name
                print(f"✅ {out_name}: {res.total_replaced} substituições aplicadas automaticamente.")
        else:
            res = ui.run(target_file, output_path=dest_file, create_backup=backup)

        summary.file_results.append(res)
        summary.total_matches_found += res.total_found
        summary.total_replacements_applied += res.total_replaced
        if res.modified:
            summary.files_modified += 1

    return summary


def spellcheck(filepath: str, dict_path: Optional[str] = None) -> None:
    """Backward-compatible entry point for the interactive spellchecker."""
    review_path(filepath, dict_path=dict_path)


__all__ = [
    "DictionaryManager",
    "HunspellClient",
    "MarkdownMasker",
    "CasePreserver",
    "ArchaicMatcher",
    "ReviewEngine",
    "InteractiveReviewUI",
    "Colors",
    "ReviewMatch",
    "ReviewAction",
    "FileReviewResult",
    "ReviewSummary",
    "review_path",
    "spellcheck",
]
