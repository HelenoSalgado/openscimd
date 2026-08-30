"""Hunspell integration client for ultra-fast Brazilian Portuguese orthographic checking."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class HunspellClient:
    """
    Subprocess-based Hunspell client communicating via pipes with 'hunspell -a'.
    Caches results in memory for maximum performance on large documents.
    """

    def __init__(self, dictionary_name: str = "pt_BR", custom_aff: Optional[Path | str] = None, custom_dic: Optional[Path | str] = None) -> None:
        self.dictionary_name = dictionary_name
        self.custom_aff = Path(custom_aff) if custom_aff else None
        self.custom_dic = Path(custom_dic) if custom_dic else None
        self.executable = shutil.which("hunspell")
        self._cache: Dict[str, Tuple[bool, List[str]]] = {}
        self._is_available = self._check_availability()

    @property
    def is_available(self) -> bool:
        """Returns True if hunspell binary and pt_BR dictionary are operational."""
        return self._is_available

    def _check_availability(self) -> bool:
        """Verifies if hunspell is executable and responsive."""
        if not self.executable:
            return False
        try:
            cmd = [self.executable, "-d", self.dictionary_name, "-a"]
            res = subprocess.run(
                cmd,
                input="^ teste\n",
                capture_output=True,
                text=True,
                timeout=2,
            )
            return res.returncode == 0 and bool(res.stdout)
        except (subprocess.SubprocessError, OSError):
            return False

    def check_word(self, word: str) -> Tuple[bool, List[str]]:
        """
        Checks a single word. Returns (is_valid, suggestions_list).
        Results are cached in-memory.
        """
        clean_word = word.strip()
        if not clean_word:
            return True, []

        cache_key = clean_word.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        results = self.check_words_batch([clean_word])
        return results.get(cache_key, (True, []))

    def check_words_batch(self, words: List[str]) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Batches multiple words through Hunspell in a single fast subprocess run.
        Uses Ispell chunking protocol delimited by double-newlines.
        Returns a mapping of lowercase_word -> (is_valid, suggestions_list).
        """
        if not self._is_available or not words:
            return {w.lower(): (True, []) for w in words}

        # Filter out words already in cache
        uncached: List[str] = []
        for w in words:
            k = w.strip().lower()
            if k and k not in self._cache:
                uncached.append(w.strip())

        if not uncached:
            return {w.lower(): self._cache.get(w.lower(), (True, [])) for w in words}

        # Deduplicate while preserving order for input pipe
        unique_uncached = list(dict.fromkeys(uncached))
        payload = "\n".join(f"^ {w}" for w in unique_uncached) + "\n"

        cmd = [self.executable, "-d", self.dictionary_name, "-a"]
        try:
            proc = subprocess.run(
                cmd,
                input=payload,
                capture_output=True,
                text=True,
                timeout=15,
            )
            stdout = proc.stdout
        except (subprocess.SubprocessError, OSError):
            # Fallback gracefully
            return {w.lower(): (True, []) for w in words}

        # Split output chunks by double newline
        # The first line of stdout is the version header: @(#) International Ispell Version...
        if "\n" in stdout:
            _, body = stdout.split("\n", 1)
        else:
            body = stdout

        chunks = body.strip().split("\n\n")

        for i, word in enumerate(unique_uncached):
            key = word.lower()
            if i < len(chunks):
                chunk = chunks[i]
                lines = [line.strip() for line in chunk.splitlines() if line.strip()]
                is_valid = bool(lines) and all(l.startswith(("*", "+", "-")) for l in lines)
                suggestions: List[str] = []
                for l in lines:
                    if l.startswith("&"):
                        parts = l.split(":", 1)
                        if len(parts) > 1:
                            suggestions.extend([s.strip() for s in parts[1].split(",") if s.strip()])

                self._cache[key] = (is_valid, suggestions)
            else:
                self._cache[key] = (True, [])

        return {w.lower(): self._cache.get(w.lower(), (True, [])) for w in words}
