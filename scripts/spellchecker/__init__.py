"""OpenSciMD Spellchecker and Archaic Orthography Review System."""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from scripts.spellchecker.dictionary import DictionaryManager
from scripts.spellchecker.engine import ReviewEngine
from scripts.spellchecker.hunspell_client import HunspellClient
from scripts.spellchecker.masker import MarkdownMasker
from scripts.spellchecker.matcher import ArchaicMatcher, CasePreserver
from scripts.spellchecker.models import FileReviewResult, ReviewAction, ReviewMatch, ReviewSummary
from scripts.spellchecker.ui import Colors, InteractiveReviewUI


def format_dry_run_report(res: FileReviewResult) -> str:
    """Formats a detailed report of detected words in dry-run/check mode."""
    if not res.matches:
        return f"[{'✅'}] {res.filepath}: 0 arcaísmos/erros encontrados."

    lines: List[str] = [
        f"[{'⚠️ ' if res.total_found > 0 else '✅'}] {res.filepath}: {res.total_found} arcaísmos/erros encontrados."
    ]

    dict_matches: List[ReviewMatch] = [m for m in res.matches if m.source == "dictionary"]
    hunspell_matches: List[ReviewMatch] = [m for m in res.matches if m.source == "hunspell"]

    def _group_matches(matches: List[ReviewMatch]) -> List[Tuple[str, List[ReviewMatch]]]:
        grouped: Dict[str, List[ReviewMatch]] = {}
        for m in matches:
            key = m.original_text.lower()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(m)
        return list(grouped.items())

    def _format_lines(group: List[ReviewMatch]) -> str:
        total_occ = len(group)
        unique_lines = sorted(set(m.line_number for m in group))
        if total_occ == 1:
            return f"(l. {unique_lines[0]})"
        elif len(unique_lines) <= 5:
            return f"({total_occ}x: l. {', '.join(str(l) for l in unique_lines)})"
        else:
            first_five = ", ".join(str(l) for l in unique_lines[:5])
            return f"({total_occ}x: l. {first_five}, ...)"

    if dict_matches:
        lines.append(f"\n  {Colors.BOLD}📖 Dicionário Curado ({len(dict_matches)} ocorrências):{Colors.ENDC}")
        for _, group in _group_matches(dict_matches):
            rep = group[0]
            line_str = _format_lines(group)
            lines.append(f"    • {Colors.BOLD}{rep.original_text}{Colors.ENDC} ➔ \"{rep.suggested_text}\" {Colors.DIM}{line_str}{Colors.ENDC}")

    if hunspell_matches:
        lines.append(f"\n  {Colors.BOLD}🔍 Hunspell / Não Reconhecidas ou Estrangeiras ({len(hunspell_matches)} ocorrências):{Colors.ENDC}")
        for _, group in _group_matches(hunspell_matches):
            rep = group[0]
            line_str = _format_lines(group)
            suggs = rep.suggestions[:3]
            sugg_str = f"➔ sugestões: {', '.join(suggs)}" if suggs else "(sem sugestões)"
            lines.append(f"    • {Colors.BOLD}{rep.original_text}{Colors.ENDC} {sugg_str} {Colors.DIM}{line_str}{Colors.ENDC}")

    return "\n".join(lines)


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
            print(format_dry_run_report(res))
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
    "format_dry_run_report",
    "review_path",
    "spellcheck",
]
