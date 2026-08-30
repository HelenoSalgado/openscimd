"""Review engine for scanning, processing, and modifying files with output path preservation."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from scripts.spellchecker.dictionary import DictionaryManager
from scripts.spellchecker.hunspell_client import HunspellClient
from scripts.spellchecker.matcher import ArchaicMatcher
from scripts.spellchecker.models import FileReviewResult, ReviewMatch, ReviewSummary


class ReviewEngine:
    """Core review engine handling document scanning, Hunspell, and text transformations."""

    def __init__(
        self,
        dict_manager: Optional[DictionaryManager] = None,
        hunspell_client: Optional[HunspellClient] = None,
        use_hunspell: bool = True,
    ) -> None:
        self.dict_manager = dict_manager or DictionaryManager()
        self.hunspell_client = hunspell_client or HunspellClient()
        self.use_hunspell = use_hunspell
        self._matcher = ArchaicMatcher(
            self.dict_manager.entries,
            hunspell_client=self.hunspell_client if self.use_hunspell else None,
            ignored_words=self.dict_manager.ignored_words,
        )

    def reload(self) -> None:
        """Reloads dictionary and recompiles patterns."""
        self.dict_manager.reload()
        self._matcher = ArchaicMatcher(
            self.dict_manager.entries,
            hunspell_client=self.hunspell_client if self.use_hunspell else None,
            ignored_words=self.dict_manager.ignored_words,
        )

    def scan_text(self, text: str, mask_markdown: bool = True) -> List[ReviewMatch]:
        """Scans a text string for archaic and spelling terms."""
        return self._matcher.find_matches(
            text,
            mask_markdown=mask_markdown,
            use_hunspell=self.use_hunspell,
        )

    def scan_file(self, filepath: Path | str, mask_markdown: bool = True) -> List[ReviewMatch]:
        """Reads a file and returns all spelling/archaic matches."""
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.scan_text(content, mask_markdown=mask_markdown)

    @classmethod
    def apply_replacements(cls, original_content: str, replacements: List[Tuple[int, int, str]]) -> str:
        """
        Applies a list of non-overlapping (start, end, new_text) substitutions.
        Replacements are applied in reverse order to preserve string indices.
        """
        if not replacements:
            return original_content

        # Sort replacements by start index descending
        sorted_replacements = sorted(replacements, key=lambda x: x[0], reverse=True)

        content = original_content
        for start, end, new_text in sorted_replacements:
            content = content[:start] + new_text + content[end:]

        return content

    def auto_apply_file(
        self,
        filepath: Path | str,
        output_path: Optional[Path | str] = None,
        create_backup: bool = False,
    ) -> FileReviewResult:
        """
        Automatically applies all dictionary matches in a file.
        If output_path is specified, saves the modified version to output_path and preserves original.
        """
        path = Path(filepath)
        dest_path = Path(output_path) if output_path else path
        matches = self.scan_file(path)
        result = FileReviewResult(filepath=path, output_filepath=dest_path, total_found=len(matches), matches=matches)

        if not matches:
            if dest_path != path:
                # Copy file to output destination if distinct
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest_path)
            return result

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # In-place backup if writing directly over original
        if dest_path == path and create_backup:
            backup_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup_path)

        replacements = [(m.start, m.end, m.suggested_text) for m in matches]
        updated_content = self.apply_replacements(content, replacements)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        result.total_replaced = len(matches)
        result.modified = True
        return result

    def dry_run_file(self, filepath: Path | str) -> FileReviewResult:
        """
        Scans a file in check/dry-run mode without modifying any files.
        """
        path = Path(filepath)
        matches = self.scan_file(path)
        return FileReviewResult(
            filepath=path,
            total_found=len(matches),
            total_replaced=0,
            total_skipped=len(matches),
            modified=False,
            matches=matches,
        )
