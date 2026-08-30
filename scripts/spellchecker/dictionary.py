"""Dictionary management for archaic spelling, personal overrides, and persistent ignore lists."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Set


class DictionaryManager:
    """Manages loading, merging, validating, and saving orthographic dictionaries and ignored words."""

    DEFAULT_BASE_DICT = Path(__file__).resolve().parent.parent / "data" / "dicionario_arcaico.json"
    DEFAULT_PERSONAL_DICT = Path(__file__).resolve().parent.parent / "data" / "dicionario_pessoal.json"
    DEFAULT_IGNORED_PATH = Path(__file__).resolve().parent.parent / "data" / "dicionario_ignorado.json"

    def __init__(
        self,
        base_dict_path: Optional[Path | str] = None,
        personal_dict_path: Optional[Path | str] = None,
        custom_dict_paths: Optional[Iterable[Path | str]] = None,
        ignored_path: Optional[Path | str] = None,
    ) -> None:
        self.base_dict_path = Path(base_dict_path) if base_dict_path else self.DEFAULT_BASE_DICT
        self.personal_dict_path = Path(personal_dict_path) if personal_dict_path else self.DEFAULT_PERSONAL_DICT
        self.ignored_path = Path(ignored_path) if ignored_path else self.DEFAULT_IGNORED_PATH
        self.custom_dict_paths = [Path(p) for p in custom_dict_paths] if custom_dict_paths else []
        self._entries: Dict[str, str] = {}
        self._ignored_words: Set[str] = set()
        self.reload()

    @property
    def entries(self) -> Dict[str, str]:
        """Returns the active mapping of archaic terms to modern equivalents."""
        return self._entries

    @property
    def ignored_words(self) -> Set[str]:
        """Returns the set of persistently ignored words."""
        return self._ignored_words

    def reload(self) -> None:
        """Loads and merges all configured dictionaries and ignored lists."""
        merged: Dict[str, str] = {}

        # 1. Base dictionary
        if self.base_dict_path and self.base_dict_path.is_file():
            base_data = self.load_file(self.base_dict_path)
            merged.update(base_data)

        # 2. Personal dictionary (takes precedence over base)
        if self.personal_dict_path and self.personal_dict_path.is_file():
            personal_data = self.load_file(self.personal_dict_path)
            merged.update(personal_data)

        # 3. Custom dictionaries
        for custom_path in self.custom_dict_paths:
            if custom_path.is_file():
                custom_data = self.load_file(custom_path)
                merged.update(custom_data)

        self._entries = self.sanitize_entries(merged)

        # 4. Ignored words list
        self._ignored_words = self.load_ignored_file(self.ignored_path)

    @staticmethod
    def load_file(path: Path | str) -> Dict[str, str]:
        """Loads a JSON dictionary file, ignoring corrupt entries or files."""
        filepath = Path(path)
        if not filepath.exists():
            return {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    @staticmethod
    def load_ignored_file(path: Path | str) -> Set[str]:
        """Loads a JSON array or list of ignored words."""
        filepath = Path(path)
        if not filepath.is_file():
            return set()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {str(w).strip().lower() for w in data if str(w).strip()}
        except (json.JSONDecodeError, OSError):
            pass
        return set()

    @classmethod
    def save_ignored_file(cls, path: Path | str, ignored: Set[str]) -> None:
        """Saves ignored words to a JSON file sorted alphabetically."""
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        sorted_list = sorted({w.strip().lower() for w in ignored if w.strip()})
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sorted_list, f, indent=2, ensure_ascii=False)
            f.write("\n")

    def add_ignored(self, word: str, save_to_disk: bool = True) -> bool:
        """Adds a word to the persistent ignore list."""
        clean = word.strip().lower()
        if not clean:
            return False
        self._ignored_words.add(clean)
        if save_to_disk:
            self.save_ignored_file(self.ignored_path, self._ignored_words)
        return True

    def remove_ignored(self, word: str, save_to_disk: bool = True) -> bool:
        """Removes a word from the persistent ignore list."""
        clean = word.strip().lower()
        if clean in self._ignored_words:
            self._ignored_words.remove(clean)
            if save_to_disk:
                self.save_ignored_file(self.ignored_path, self._ignored_words)
            return True
        return False

    def is_ignored(self, word: str) -> bool:
        """Returns True if the word is in the persistent ignore list."""
        return word.strip().lower() in self._ignored_words

    @classmethod
    def sanitize_entries(cls, raw_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Cleans dictionary entries:
        - Normalizes keys to stripped lowercase.
        - Strips values.
        - Removes identity mappings where key == value (case-insensitively).
        - Removes empty keys or values.
        """
        sanitized: Dict[str, str] = {}
        for key, value in raw_dict.items():
            k = key.strip().lower()
            v = value.strip()
            if not k or not v:
                continue
            if k == v.lower():
                continue
            sanitized[k] = v
        return sanitized

    def get_replacement(self, word: str) -> Optional[str]:
        """Gets modern replacement for an archaic term if available."""
        return self._entries.get(word.strip().lower())

    def add_entry(
        self,
        key: str,
        value: str,
        target_path: Optional[Path | str] = None,
        save_to_disk: bool = True,
    ) -> bool:
        """Adds a new entry to the personal dictionary."""
        k = key.strip().lower()
        v = value.strip()
        if not k or not v or k == v.lower():
            return False

        self._entries[k] = v

        if save_to_disk:
            dest = Path(target_path) if target_path else self.personal_dict_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            existing = self.load_file(dest)
            existing[k] = v
            sanitized = self.sanitize_entries(existing)
            self.save_file(dest, sanitized)

        return True

    def remove_entry(
        self,
        key: str,
        from_file: bool = True,
    ) -> bool:
        """Removes an entry from the active dictionary and all underlying files."""
        k = key.strip().lower()
        removed = False
        if k in self._entries:
            del self._entries[k]
            removed = True

        if from_file:
            all_paths = [self.base_dict_path, self.personal_dict_path] + self.custom_dict_paths
            for p in all_paths:
                if p and p.is_file():
                    data = self.load_file(p)
                    if k in data or any(dk.lower() == k for dk in data):
                        data = {dk: dv for dk, dv in data.items() if dk.lower() != k}
                        self.save_file(p, data)
                        removed = True

        return removed

    @classmethod
    def save_file(cls, path: Path | str, data: Dict[str, str]) -> None:
        """Saves dictionary data to a JSON file sorted alphabetically."""
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        sanitized = cls.sanitize_entries(data)
        sorted_dict = dict(sorted(sanitized.items(), key=lambda x: x[0].lower()))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sorted_dict, f, indent=4, ensure_ascii=False)
            f.write("\n")
