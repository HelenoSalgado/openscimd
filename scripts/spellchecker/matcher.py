"""Pattern matching and case preservation for archaic text review with Hunspell support and ignore lists."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from scripts.spellchecker.hunspell_client import HunspellClient
from scripts.spellchecker.masker import MarkdownMasker
from scripts.spellchecker.models import ReviewMatch


class CasePreserver:
    """Handles intelligent casing transformation for orthographic replacements."""

    @classmethod
    def preserve_case(cls, original: str, replacement: str) -> str:
        """
        Adapts the casing of `replacement` to match the casing style of `original`.
        
        Rules:
        - ALL CAPS ('ACTIVO' -> 'ATIVO', 'VOSSA MERCÊ' -> 'VOCÊ')
        - Title Case ('Activo' -> 'Ativo', 'Vossa MercÊ' -> 'Você')
        - Sentence Case ('Vossa mercê' -> 'Você')
        - Lowercase ('activo' -> 'ativo')
        - Explicit casing in dictionary (e.g. Proper nouns like 'Deus', 'Bíblia')
        """
        if not original or not replacement:
            return replacement

        # 1. All Uppercase
        if original.isupper():
            return replacement.upper()

        # 2. Capitalized / Title Case
        if original[0].isupper():
            orig_words = [w for w in re.split(r'[\s\-]+', original) if w]
            # Multi-word: check if all words are capitalized
            if len(orig_words) > 1 and all(w[0].isupper() for w in orig_words):
                # Capitalize each word
                return " ".join(w[:1].upper() + w[1:] for w in replacement.split())
            else:
                # Capitalize first character
                return replacement[:1].upper() + replacement[1:]

        # 3. All Lowercase
        if original.islower():
            # If replacement has deliberate internal capitals (e.g. Proper nouns), keep them
            if any(c.isupper() for c in replacement):
                return replacement
            return replacement.lower()

        return replacement


class ArchaicMatcher:
    """Scans text for archaic terms and phrases using dictionary mappings and Hunspell."""

    def __init__(
        self,
        dictionary: Dict[str, str],
        hunspell_client: Optional[HunspellClient] = None,
        ignored_words: Optional[Set[str]] = None,
    ) -> None:
        self.dictionary = {k.strip().lower(): v.strip() for k, v in dictionary.items() if k.strip().lower() != v.strip().lower()}
        self.hunspell_client = hunspell_client
        self.ignored_words = {w.strip().lower() for w in ignored_words} if ignored_words else set()
        self._compiled_patterns = self._build_patterns()

    def _build_patterns(self) -> List[Tuple[re.Pattern[str], str]]:
        """Compiles regex patterns sorted by key length descending."""
        patterns: List[Tuple[re.Pattern[str], str]] = []

        # Sort keys by length descending to match longer expressions first
        sorted_keys = sorted(self.dictionary.keys(), key=lambda k: len(k), reverse=True)

        for key in sorted_keys:
            if key in self.ignored_words:
                continue

            parts = re.split(r'(\s+|[\-’\'])', key)
            pattern_parts = []
            for p in parts:
                if not p:
                    continue
                if p.isspace():
                    pattern_parts.append(r'\s+')
                elif p in ("'", "’"):
                    pattern_parts.append(r"['’]")
                elif p == "-":
                    pattern_parts.append(r"\s*-\s*")
                else:
                    pattern_parts.append(re.escape(p))

            regex_str = r"(?<!\w)" + "".join(pattern_parts) + r"(?!\w)"
            try:
                compiled = re.compile(regex_str, re.IGNORECASE)
                patterns.append((compiled, key))
            except re.error:
                continue

        return patterns

    def find_matches(
        self,
        text: str,
        mask_markdown: bool = True,
        use_hunspell: bool = True,
    ) -> List[ReviewMatch]:
        """
        Finds all non-overlapping archaic/spelling matches in the text.
        Combines Curated Dictionary (Phase 1) and Hunspell (Phase 2).
        """
        scan_text = MarkdownMasker.mask(text) if mask_markdown else text
        raw_matches: List[Tuple[int, int, str, str, str, str, List[str]]] = []

        # -------------------------------------------------------------
        # Phase 1: Curated Dictionary matching (including phrases)
        # -------------------------------------------------------------
        matched_spans: List[Tuple[int, int]] = []

        for pattern, dict_key in self._compiled_patterns:
            if dict_key in self.ignored_words:
                continue

            target_replacement = self.dictionary[dict_key]
            for m in pattern.finditer(scan_text):
                start, end = m.start(), m.end()
                original_text = text[start:end]
                if original_text.lower() in self.ignored_words:
                    continue

                suggested_text = CasePreserver.preserve_case(original_text, target_replacement)

                # Skip identity replacements (e.g. 'homem' -> 'homem')
                if original_text == suggested_text:
                    continue

                raw_matches.append((start, end, original_text, suggested_text, dict_key, "dictionary", [suggested_text]))
                matched_spans.append((start, end))

        # -------------------------------------------------------------
        # Phase 2: Hunspell Morphological & Spelling Discovery
        # -------------------------------------------------------------
        if use_hunspell and self.hunspell_client and self.hunspell_client.is_available:
            word_pattern = re.compile(r'\b[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*\b')
            candidates: List[Tuple[int, int, str]] = []

            for m in word_pattern.finditer(scan_text):
                start, end = m.start(), m.end()
                # Skip if already inside a dictionary match span
                if any(sp_start <= start and end <= sp_end for sp_start, sp_end in matched_spans):
                    continue

                word = text[start:end]
                k = word.lower()
                # Skip very short words, known dictionary keys, or ignored words
                if len(word) <= 2 or k in self.dictionary or k in self.ignored_words:
                    continue

                candidates.append((start, end, word))

            if candidates:
                words_to_check = [c[2] for c in candidates]
                check_results = self.hunspell_client.check_words_batch(words_to_check)

                for start, end, original_text in candidates:
                    key = original_text.lower()
                    if key in self.ignored_words:
                        continue

                    is_valid, raw_suggestions = check_results.get(key, (True, []))

                    if not is_valid and raw_suggestions:
                        # Format suggestions with proper casing
                        preserved_suggs = [
                            CasePreserver.preserve_case(original_text, s)
                            for s in raw_suggestions
                            if s.lower() != key
                        ]
                        if preserved_suggs:
                            top_suggestion = preserved_suggs[0]
                            if original_text != top_suggestion:
                                raw_matches.append((
                                    start,
                                    end,
                                    original_text,
                                    top_suggestion,
                                    key,
                                    "hunspell",
                                    preserved_suggs[:5],
                                ))

        # Sort by start position
        raw_matches.sort(key=lambda x: x[0])

        # Filter out overlaps (prioritizing dictionary matches / earlier matches)
        filtered_matches: List[Tuple[int, int, str, str, str, str, List[str]]] = []
        last_end = -1
        for start, end, orig, sugg, k, source, suggs in raw_matches:
            if start >= last_end:
                filtered_matches.append((start, end, orig, sugg, k, source, suggs))
                last_end = end

        # Construct ReviewMatch objects with line and context info
        results: List[ReviewMatch] = []
        for start, end, original_text, suggested_text, dict_key, source, suggestions in filtered_matches:
            line_num = text.count("\n", 0, start) + 1
            line_start = text.rfind("\n", 0, start)
            line_start = 0 if line_start == -1 else line_start + 1
            line_end = text.find("\n", end)
            line_end = len(text) if line_end == -1 else line_end

            col_num = start - line_start + 1
            line_content = text[line_start:line_end]

            ctx_start = max(0, start - 60)
            ctx_end = min(len(text), end + 60)
            context_before = text[ctx_start:start].replace("\n", " ")
            context_after = text[end:ctx_end].replace("\n", " ")

            results.append(
                ReviewMatch(
                    start=start,
                    end=end,
                    original_text=original_text,
                    suggested_text=suggested_text,
                    dict_key=dict_key,
                    line_number=line_num,
                    column_number=col_num,
                    line_content=line_content,
                    context_before=context_before,
                    context_after=context_after,
                    source=source,
                    suggestions=suggestions,
                )
            )

        return results
