"""Data models and structures for the archaic spelling review system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ReviewAction(str, Enum):
    """Actions available during interactive review."""
    REPLACE = "s"             # [s]im - Apply current replacement
    SKIP = "n"                # [n]ão - Skip this match
    REPLACE_ALL = "t"         # [t]odas - Replace all occurrences in whole document
    IGNORE_ALL = "i"          # [i]gnorar todas - Ignore all occurrences in whole document
    EDIT = "e"                # [e]ditar - Custom replacement string
    DELETE_FROM_DICT = "d"    # [d]eletar regra - Remove key from dictionary
    UNDO = "u"                # [u]ndo - Revert previous action
    QUIT = "q"                # [q]uit - Exit review session


@dataclass
class ReviewMatch:
    """Represents a single match found in a document."""
    start: int
    end: int
    original_text: str
    suggested_text: str
    dict_key: str
    line_number: int
    column_number: int
    line_content: str
    context_before: str = ""
    context_after: str = ""
    source: str = "dictionary"  # "dictionary" or "hunspell"
    suggestions: List[str] = field(default_factory=list)
    applied_replacement: Optional[str] = None

    @property
    def is_identity(self) -> bool:
        """Returns True if the suggested text is identical to original text."""
        return self.original_text == self.suggested_text


@dataclass
class FileReviewResult:
    """Summary of changes and statistics for a reviewed file."""
    filepath: Path
    output_filepath: Optional[Path] = None
    total_found: int = 0
    total_replaced: int = 0
    total_skipped: int = 0
    modified: bool = False
    matches: List[ReviewMatch] = field(default_factory=list)


@dataclass
class ReviewSummary:
    """Aggregated summary of multiple reviewed files."""
    files_processed: int = 0
    files_modified: int = 0
    total_matches_found: int = 0
    total_replacements_applied: int = 0
    file_results: List[FileReviewResult] = field(default_factory=list)
