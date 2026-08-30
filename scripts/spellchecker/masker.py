"""Markdown masking utility to ignore code blocks, frontmatter, links, math, and tags while preserving 1:1 text offsets."""

from __future__ import annotations

import re


class MarkdownMasker:
    """
    Masks non-prose Markdown content with spaces while preserving
    exact character lengths and line breaks, ensuring 1:1 offset mapping.
    """

    @classmethod
    def mask(cls, text: str) -> str:
        """
        Returns a copy of the input text where code blocks, frontmatter,
        links, math formulas, and HTML tags are replaced with spaces.
        """
        chars = list(text)

        def blank_out(start: int, end: int) -> None:
            for i in range(max(0, start), min(len(chars), end)):
                if chars[i] != "\n":
                    chars[i] = " "

        # 1. Frontmatter (YAML delimited by --- at start of document)
        fm = re.match(r"^---\r?\n[\s\S]*?\r?\n---\r?\n", text)
        if fm:
            blank_out(0, fm.end())

        # 2. Fenced code blocks (``` or ~~~)
        for m in re.finditer(r"(```|~~~)[^\n]*\n[\s\S]*?\n\1", text):
            blank_out(m.start(), m.end())

        # 3. HTML comments
        for m in re.finditer(r"<!--[\s\S]*?-->", text):
            blank_out(m.start(), m.end())

        # 4. LaTeX Math blocks ($$...$$)
        for m in re.finditer(r"\$\$[\s\S]*?\$\$", text):
            blank_out(m.start(), m.end())

        # 5. Inline LaTeX math ($...$)
        for m in re.finditer(r"(?<!\$)\$(?!\$)((?:\\.|[^\$\\\n])+)\$(?!\$)", text):
            blank_out(m.start(), m.end())

        # 6. Inline code (`...` or ``...``)
        for m in re.finditer(r"`+[^`\n]+`+", text):
            blank_out(m.start(), m.end())

        # 7. Images ![alt](url)
        for m in re.finditer(r"!\[[^\]]*\]\([^)]+\)", text):
            blank_out(m.start(), m.end())

        # 8. Link destinations [text](url) - mask only the (url) part
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            blank_out(m.start(2) - 1, m.end(2) + 1)

        # 9. Autolinks <http://...> or <https://...>
        for m in re.finditer(r"<(?:https?|mailto):[^>]+>", text):
            blank_out(m.start(), m.end())

        # 10. HTML tags <tag...> and </tag>
        for m in re.finditer(r"<[a-zA-Z\/][^>]*>", text):
            blank_out(m.start(), m.end())

        # 11. Footnote references [^1]
        for m in re.finditer(r"\[\^[^\]]+\]", text):
            blank_out(m.start(), m.end())

        return "".join(chars)
