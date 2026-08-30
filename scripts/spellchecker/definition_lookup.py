"""Inline Portuguese dictionary definition lookup with local caching."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup


class DefinitionLookup:
    """Fetches and caches definitions from Dicio / Portuguese lexical resources."""

    CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "dicionario_definicoes_cache.json"

    def __init__(self, cache_file: Optional[Path | str] = None) -> None:
        self.cache_file = Path(cache_file) if cache_file else self.CACHE_FILE
        self._cache: Dict[str, Dict[str, str]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        """Loads cached definitions from disk."""
        if not self.cache_file.is_file():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self) -> None:
        """Saves cached definitions to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(dict(sorted(self._cache.items())), f, indent=2, ensure_ascii=False)
                f.write("\n")
        except OSError:
            pass

    def get_definition(self, word: str) -> Optional[Dict[str, str]]:
        """
        Retrieves the definition of a word.
        Returns a dict with 'word', 'meaning', 'class', 'etymology', 'notes', or None if not found.
        """
        clean_word = word.strip().lower()
        if not clean_word:
            return None

        # Check local cache first (instant & offline)
        if clean_word in self._cache:
            return self._cache[clean_word]

        # Fetch online from Dicio.com.br
        url = f"https://www.dicio.com.br/{clean_word}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; OpenSciMD-CLI) AppleWebKit/537.36 (KHTML, like Gecko)"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            meaning_p = soup.find("p", class_="significado")
            if not meaning_p:
                return None

            raw_text = meaning_p.get_text("\n", strip=True)
            
            # Extract grammatical class (e.g. 'substantivo masculino', 'verbo transitivo', 'adjetivo')
            gram_class = ""
            meaning_lines: List[str] = []
            etymology = ""
            ortho_notes = ""

            for line in raw_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith(("substantivo", "verbo", "adjetivo", "advérbio", "pronome", "conjunção", "preposição", "interjeição")):
                    if not gram_class:
                        gram_class = line
                    else:
                        meaning_lines.append(f"• [{line}]")
                elif "Etimologia" in line or "origem da palavra" in line:
                    etymology = line
                elif "Forma alterada após Acordo Ortográfico" in line or "Grafia alterada" in line:
                    ortho_notes = line
                else:
                    meaning_lines.append(line)

            entry = {
                "word": clean_word,
                "class": gram_class,
                "meaning": "\n".join(meaning_lines),
                "etymology": etymology,
                "notes": ortho_notes,
            }

            self._cache[clean_word] = entry
            self._save_cache()
            return entry

        except (requests.RequestException, Exception):
            return None
