"""Linter editorial determinístico e comparador estrutural contra fonte local."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from bs4 import BeautifulSoup

from scripts.biblical_books import iter_biblical_reference_matches
from scripts.utils import parse_markdown_file

Severity = Literal["error", "warning"]

_ROMAN_NUMERAL_RE = re.compile(
    r"^M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$"
)

_ALLOWED_HEADING_ACRONYMS: frozenset[str] = frozenset(
    {
        "ABNT",
        "API",
        "ARA",
        "BBK",
        "BM25",
        "CAG",
        "CDU",
        "CLI",
        "CPU",
        "DOI",
        "EPUB",
        "ESV",
        "FTS5",
        "GPU",
        "HTML",
        "HTTP",
        "HTTPS",
        "IBGE",
        "IPDA",
        "ISBN",
        "ISO",
        "ISSN",
        "JSON",
        "KDP",
        "KJV",
        "LLM",
        "LLMS",
        "LXX",
        "MEC",
        "NA28",
        "NLP",
        "NVI",
        "OCR",
        "ORCID",
        "PDF",
        "PLN",
        "RAG",
        "SBB",
        "SBLGNT",
        "SQL",
        "TOC",
        "UDC",
        "UFSC",
        "URL",
        "UTF",
        "VRAM",
        "XML",
        "YAML",
    }
)

_ABBREV_BEFORE_DOT_RE = re.compile(
    r"\b(?:"
    r"etc|a\.C|d\.C|Cf|cf|op\.\s*cit|loc\.\s*cit|ibid|ib|et\s+al|"
    r"N\.\s*T|A\.\s*T|ms|mss|"
    r"e\.g|i\.e|pp|p|vv|v|vol|cap|art|n|s\.v|ed|trad|org|Jr|Sr|Dr|St|S|N"
    r")\.$"
)

_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([a-zA-Z0-9_-]+)\]:")
_FOOTNOTE_ANY_RE = re.compile(r"\[\^([a-zA-Z0-9_-]+)\]")
_NUMERIC_RANGE_HYPHEN_RE = re.compile(r"(?<![A-Za-zÀ-ÿ0-9_/-])(\d+)-(\d+)(?![A-Za-zÀ-ÿ0-9_/-])")
_ASCII_ELLIPSIS_RE = re.compile(r"\.{3,}|\.\s+\.\s+\.")
_OCR_ZERO_IN_WORD_RE = re.compile(r"\b[a-zà-ÿA-ZÀ-Ÿ]*[a-zà-ÿ]0[a-zà-ÿ][a-zà-ÿA-ZÀ-Ÿ]*\b")
_DUPLICATE_WORD_RE = re.compile(r"\b([a-zà-ÿ]{3,})\s+\1\b", re.IGNORECASE)
_BQ_PREFIX_RE = re.compile(r"^((?:\s*>\s*)*)(.*)$")
_LIST_ITEM_RE = re.compile(r"^(\s*)(?:([-*+])|(\d+)\.)\s+\S")
_NOTES_APPARATUS_HEADING_RE = re.compile(r"^Notas(?:\s+(?:do|da|dos|das|Editoriais)\b|\s*$)", re.IGNORECASE)
_BIBLIOGRAPHY_HEADING_RE = re.compile(
    r"^(?:Bibliografia|Referências(?:\s+Bibliográficas)?|Conspectus\s+Librorum|Obras\s+Citadas|Fontes\s+Bibliográficas)\b",
    re.IGNORECASE,
)
_IGNORE_DIRECTIVE_RE = re.compile(r"<!--\s*openscimd-ignore\s*:\s*([A-Za-z0-9_,\s-]+?)\s*-->", re.IGNORECASE)


@dataclass(frozen=True)
class EditorialIssue:
    """Representa um achado editorial ou estrutural em um arquivo Markdown."""

    code: str
    severity: Severity
    line: int | None
    message: str
    excerpt: str = ""


@dataclass(frozen=True)
class SourceMetrics:
    """Métricas estruturais básicas extraídas de um documento."""

    words: int
    paragraphs: int
    headings: int
    author_footnotes: int


@dataclass(frozen=True)
class SourceComparisonReport:
    """Resultado da comparação quantitativa entre matriz original e revisão."""

    source_metrics: SourceMetrics
    review_metrics: SourceMetrics
    word_ratio: float
    issues: list[EditorialIssue] = field(default_factory=list)


@dataclass(frozen=True)
class LintReport:
    """Relatório consolidado do linter editorial para um documento."""

    file_path: Path
    issues: list[EditorialIssue] = field(default_factory=list)
    comparison: SourceComparisonReport | None = None

    @property
    def all_issues(self) -> list[EditorialIssue]:
        if self.comparison is None:
            return list(self.issues)
        return [*self.issues, *self.comparison.issues]

    @property
    def errors(self) -> list[EditorialIssue]:
        return [issue for issue in self.all_issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[EditorialIssue]:
        return [issue for issue in self.all_issues if issue.severity == "warning"]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _mask_non_prose(text: str, keep_footnotes: bool = False) -> str:
    """Mascara Frontmatter, blocos de código, matemática, links/URLs e tags mantendo índices 1:1."""
    chars = list(text)

    def blank_out(start: int, end: int) -> None:
        for idx in range(max(0, start), min(len(chars), end)):
            if chars[idx] != "\n":
                chars[idx] = " "

    fm = re.match(r"^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)", text)
    if fm:
        blank_out(0, fm.end())

    for m in re.finditer(r"(```|~~~)[^\n]*\n[\s\S]*?\n\1", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"<!--[\s\S]*?-->", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"\$\$[\s\S]*?\$\$", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"(?<!\$)\$(?!\$)((?:\\.|[^\$\\\n])+)\$(?!\$)", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"`+[^`\n]+`+", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"!\[[^\]]*\]\([^)]+\)", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        blank_out(m.start(2) - 1, m.end(2) + 1)

    for m in re.finditer(r"<(?:https?|mailto):[^>]+>", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"https?://[^\s)>\]\"']+", text):
        blank_out(m.start(), m.end())

    for m in re.finditer(r"<[a-zA-Z/][^>]*>", text):
        blank_out(m.start(), m.end())

    if not keep_footnotes:
        for m in re.finditer(r"\[\^[^\]]+\]", text):
            blank_out(m.start(), m.end())

    return "".join(chars)


def _is_roman_numeral(token: str) -> bool:
    return bool(token) and bool(_ROMAN_NUMERAL_RE.fullmatch(token))


def _strip_heading_markup(raw_heading: str) -> str:
    """Remove âncoras e marcações inline de um cabeçalho antes da análise lexical."""
    cleaned = re.sub(r"\[\^[^\]]+\]", "", raw_heading)
    return re.sub(r"[*_`]", "", cleaned).strip()


def _find_notes_start_line(masked_with_fn_lines: list[str]) -> int | None:
    """Identifica a linha 1-based onde inicia o aparato pós-texto de notas."""
    first_def_idx: int | None = None
    for idx, line in enumerate(masked_with_fn_lines):
        if _FOOTNOTE_DEF_RE.match(line):
            first_def_idx = idx
            break
    if first_def_idx is None:
        return None

    for back in range(first_def_idx - 1, -1, -1):
        stripped = masked_with_fn_lines[back].strip()
        if not stripped:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m and _NOTES_APPARATUS_HEADING_RE.match(_strip_heading_markup(m.group(2))):
            return back + 1
        break

    return first_def_idx + 1


def _check_headings(
    masked_lines: list[str],
    notes_start_line: int | None = None,
) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    body_prev_level = 1
    body_first_heading_seen = False
    in_post_text = False
    post_prev_level: int | None = None

    for line_no, line in enumerate(masked_lines, start=1):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue

        hashes, raw_heading = m.group(1), m.group(2).strip()
        level = len(hashes)
        clean_heading = _strip_heading_markup(raw_heading)

        if not in_post_text and (
            (notes_start_line is not None and line_no >= notes_start_line)
            or bool(_BIBLIOGRAPHY_HEADING_RE.match(clean_heading))
        ):
            in_post_text = True

        if level == 1:
            issues.append(
                EditorialIssue(
                    code="ED001",
                    severity="error",
                    line=line_no,
                    message="Cabeçalho H1 ('# ') é proibido no corpo; o título principal pertence ao YAML.",
                    excerpt=line.strip()[:80],
                )
            )
            if in_post_text:
                post_prev_level = 1
            else:
                body_prev_level = 1
                body_first_heading_seen = True
            continue

        if re.search(r"\*\*[^*]+\*\*|__[^_]+__", raw_heading):
            issues.append(
                EditorialIssue(
                    code="ED002",
                    severity="error",
                    line=line_no,
                    message="Negrito é proibido em cabeçalhos ('##', '###'). Use itálico quando estilístico.",
                    excerpt=line.strip()[:80],
                )
            )

        alpha_tokens = re.findall(r"[A-Za-zÀ-ÿ]+", clean_heading)
        has_long_allcaps = any(
            len(tok) >= 4
            and tok.isupper()
            and not _is_roman_numeral(tok)
            and tok not in _ALLOWED_HEADING_ACRONYMS
            for tok in alpha_tokens
        )
        non_trivial_tokens = [
            tok for tok in alpha_tokens if len(tok) >= 2 and not _is_roman_numeral(tok) and tok not in _ALLOWED_HEADING_ACRONYMS
        ]
        all_non_trivial_upper = len(non_trivial_tokens) >= 2 and all(tok.isupper() for tok in non_trivial_tokens)

        if has_long_allcaps or all_non_trivial_upper:
            issues.append(
                EditorialIssue(
                    code="ED003",
                    severity="error",
                    line=line_no,
                    message="Cabeçalho em CAIXA ALTA viola Title Case (exceção apenas para algarismos romanos).",
                    excerpt=line.strip()[:80],
                )
            )

        if not in_post_text:
            if not body_first_heading_seen and level > 2:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Primeiro cabeçalho do corpo usa nível {hashes} em vez de '##'.",
                        excerpt=line.strip()[:80],
                    )
                )
            elif body_first_heading_seen and level > body_prev_level + 1:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Salto hierárquico de cabeçalho ({'#' * body_prev_level} -> {hashes}).",
                        excerpt=line.strip()[:80],
                    )
                )
            elif level >= 6:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Nível de cabeçalho excessivo ({hashes}); limite máximo recomendado é '#####'.",
                        excerpt=line.strip()[:80],
                    )
                )

            body_prev_level = level
            body_first_heading_seen = True
        else:
            if _NOTES_APPARATUS_HEADING_RE.match(clean_heading):
                if level >= 4:
                    issues.append(
                        EditorialIssue(
                            code="ED004",
                            severity="warning",
                            line=line_no,
                            message=f"Cabeçalho de notas usa nível {hashes}; use '###'.",
                            excerpt=line.strip()[:80],
                        )
                    )
            elif _BIBLIOGRAPHY_HEADING_RE.match(clean_heading):
                if level >= 4:
                    issues.append(
                        EditorialIssue(
                            code="ED004",
                            severity="warning",
                            line=line_no,
                            message=f"Cabeçalho de bibliografia/referências usa nível {hashes}; use '##' ou '###'.",
                            excerpt=line.strip()[:80],
                        )
                    )
            elif post_prev_level is None and level > 3:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Cabeçalho de seção pós-texto usa nível {hashes}; use '##' ou '###'.",
                        excerpt=line.strip()[:80],
                    )
                )
            elif post_prev_level is not None and level > post_prev_level + 1:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Salto hierárquico de cabeçalho ({'#' * post_prev_level} -> {hashes}).",
                        excerpt=line.strip()[:80],
                    )
                )
            elif level >= 6:
                issues.append(
                    EditorialIssue(
                        code="ED004",
                        severity="warning",
                        line=line_no,
                        message=f"Nível de cabeçalho excessivo ({hashes}); limite máximo recomendado é '#####'.",
                        excerpt=line.strip()[:80],
                    )
                )

            post_prev_level = level

    return issues


def _check_footnote_sequence(namespace: str, ids: list[str], severity: Severity) -> list[EditorialIssue]:
    nums = sorted({int(m.group(1)) for fn_id in ids if (m := re.fullmatch(rf"{namespace}(\d+)", fn_id))})
    if not nums:
        return []
    expected = list(range(1, nums[-1] + 1))
    missing = sorted(set(expected) - set(nums))
    if not missing:
        return []
    label = "editoriais" if namespace == "ne" else ("do tradutor" if namespace == "nt" else "do autor")
    missing_fmt = ", ".join(f"[^{namespace}{n}]" for n in missing[:5])
    return [
        EditorialIssue(
            code="ED008",
            severity=severity,
            line=None,
            message=f"Quebra de sequência nas notas {label}: ausente(s) {missing_fmt}.",
        )
    ]


def _check_footnotes(masked_with_fn_lines: list[str]) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    defined: dict[str, int] = {}
    anchored: dict[str, int] = {}
    prev_was_def = False
    first_def_line: int | None = None
    def_lines: list[int] = []

    for line_no, line in enumerate(masked_with_fn_lines, start=1):
        def_match = _FOOTNOTE_DEF_RE.match(line)
        if def_match:
            fn_id = def_match.group(1)
            if fn_id not in defined:
                defined[fn_id] = line_no
            if first_def_line is None:
                first_def_line = line_no
            def_lines.append(line_no)
            if prev_was_def:
                issues.append(
                    EditorialIssue(
                        code="ED011",
                        severity="error",
                        line=line_no,
                        message="Definições de notas consecutivas devem ser separadas por uma linha em branco.",
                        excerpt=line.strip()[:80],
                    )
                )
            prev_was_def = True
            scan_line = line[def_match.end() :]
            line_offset = def_match.end()
        else:
            prev_was_def = False
            scan_line = line
            line_offset = 0

        for m in _FOOTNOTE_ANY_RE.finditer(scan_line):
            fn_id = m.group(1)
            if fn_id not in anchored:
                anchored[fn_id] = line_no

            abs_pos = line_offset + m.start()
            if abs_pos >= 2 and line[abs_pos - 1] in (" ", "\t") and not line[:abs_pos].isspace():
                issues.append(
                    EditorialIssue(
                        code="ED009",
                        severity="error",
                        line=line_no,
                        message=f"Espaço indevido antes da âncora [^{fn_id}].",
                        excerpt=line[max(0, abs_pos - 20) : abs_pos + 15].strip(),
                    )
                )

            if abs_pos >= 1 and line[abs_pos - 1] in (",", ";", ":", "!", "?", "."):
                prev_char = line[abs_pos - 1]
                prefix = line[:abs_pos]
                if prev_char != "." or not _ABBREV_BEFORE_DOT_RE.search(prefix):
                    issues.append(
                        EditorialIssue(
                            code="ED010",
                            severity="error",
                            line=line_no,
                            message=(
                                f"Âncora [^{fn_id}] após pontuação '{prev_char}' viola o padrão ABNT/português "
                                f"(coloque a âncora antes da pontuação: palavra[^{fn_id}]{prev_char})."
                            ),
                            excerpt=line[max(0, abs_pos - 20) : abs_pos + 15].strip(),
                        )
                    )

    for fn_id, line_no in anchored.items():
        if fn_id not in defined:
            issues.append(
                EditorialIssue(
                    code="ED006",
                    severity="error",
                    line=line_no,
                    message=f"Âncora [^{fn_id}] no texto sem definição correspondente no pós-texto.",
                )
            )

    for fn_id, line_no in defined.items():
        if fn_id not in anchored:
            issues.append(
                EditorialIssue(
                    code="ED007",
                    severity="error",
                    line=line_no,
                    message=f"Definição [^{fn_id}]: órfã (sem âncora correspondente no corpo).",
                )
            )

    all_ids = sorted(set(defined.keys()) | set(anchored.keys()))
    issues.extend(_check_footnote_sequence("ne", all_ids, severity="error"))
    issues.extend(_check_footnote_sequence("nt", all_ids, severity="error"))
    issues.extend(_check_footnote_sequence("", all_ids, severity="warning"))

    if first_def_line is not None:
        # Verifica se há separador --- e cabeçalho ### Notas antes do aparato pós-texto
        pre_slice = [ln.strip() for ln in masked_with_fn_lines[: first_def_line - 1]]
        has_hr_before = "---" in pre_slice[-15:]
        has_notes_heading = any(re.match(r"^###\s+Notas\b", s, re.IGNORECASE) for s in pre_slice[-10:])
        if not has_hr_before or not has_notes_heading:
            issues.append(
                EditorialIssue(
                    code="ED012",
                    severity="warning",
                    line=first_def_line,
                    message="Aparato de notas deve ser precedido por único '---' e cabeçalho '### Notas ...'.",
                )
            )

        # Verifica separadores '---' duplicados entre definições do aparato de notas pós-texto
        last_def_line = def_lines[-1]
        post_hrs = [
            idx + 1
            for idx in range(max(0, first_def_line - 1), last_def_line)
            if masked_with_fn_lines[idx].strip() == "---"
        ]
        if post_hrs:
            issues.append(
                EditorialIssue(
                    code="ED012",
                    severity="warning",
                    line=post_hrs[0],
                    message="Separador '---' repetido dentro do aparato de notas pós-texto (use um único '---').",
                )
            )

    return issues


def _mask_structured_tokens_for_ranges(line: str) -> str:
    """Mascara datas ISO/DMY, DOIs, ISSN/ISBN e notações UDC/BBK para checagem de ED013."""
    patterns = (
        r"\b10\.\d{4,9}/\S+",
        r"(?i:\b(?:e[-_]?issn|issn|isbn)\s*:?\s*[\dX-]+)",
        r"(?i:\b(?:UDC|CDU|BBK|HoS)\s*:?\s*[^\s,;]+)",
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
    )
    masked = line
    for pat in patterns:
        masked = re.sub(pat, lambda m: " " * len(m.group(0)), masked)
    return masked


def _is_valid_portuguese_duplicate(line: str, match: re.Match[str]) -> bool:
    """Identifica construções gramaticais ou filosóficas legítimas com palavras repetidas."""
    word = match.group(1).lower()
    prefix = line[: match.start()]
    if word == "que":
        return bool(re.search(r"\bdo\s+$", prefix, re.IGNORECASE))
    if word == "nada":
        return bool(re.search(r"\b(?:do|de)\s+$", prefix, re.IGNORECASE))
    if word == "todo":
        return True
    return False


def _check_typography_and_ocr(masked_lines: list[str], masked_body: str) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []

    for line_no, line in enumerate(masked_lines, start=1):
        if '"' in line:
            issues.append(
                EditorialIssue(
                    code="ED005",
                    severity="error",
                    line=line_no,
                    message="Aspas retas '\"' proibidas no corpo; use aspas curvas (“”) ou guillemets («»).",
                    excerpt=line.strip()[:80],
                )
            )

        range_scan = _mask_structured_tokens_for_ranges(line)
        m_range = _NUMERIC_RANGE_HYPHEN_RE.search(range_scan)
        if m_range:
            issues.append(
                EditorialIssue(
                    code="ED013",
                    severity="error",
                    line=line_no,
                    message=f"Intervalo numérico '{m_range.group(0)}' usa hífen em vez de meia-risca ('–').",
                    excerpt=line[max(0, m_range.start() - 15) : m_range.end() + 15].strip(),
                )
            )

        for ref_match in iter_biblical_reference_matches(line):
            if not ref_match.is_canonical:
                issues.append(
                    EditorialIssue(
                        code="ED014",
                        severity="error",
                        line=line_no,
                        message=(
                            f"Referência bíblica '{ref_match.raw}' fora do padrão canônico "
                            f"(use '{ref_match.expected}')."
                        ),
                        excerpt=ref_match.raw,
                    )
                )

        for m_ellipsis in _ASCII_ELLIPSIS_RE.finditer(line):
            issues.append(
                EditorialIssue(
                    code="ED016",
                    severity="error",
                    line=line_no,
                    message="Reticências em pontos ASCII ('...') proibidas no corpo; use o caractere tipográfico '…' (U+2026).",
                    excerpt=line[max(0, m_ellipsis.start() - 15) : m_ellipsis.end() + 15].strip(),
                )
            )

        m_zero = _OCR_ZERO_IN_WORD_RE.search(line)
        if m_zero:
            issues.append(
                EditorialIssue(
                    code="ED015a",
                    severity="error",
                    line=line_no,
                    message=f"Possível erro de OCR: dígito '0' dentro da palavra '{m_zero.group(0)}'.",
                    excerpt=m_zero.group(0),
                )
            )

        for m_dup in _DUPLICATE_WORD_RE.finditer(line):
            if _is_valid_portuguese_duplicate(line, m_dup):
                continue
            issues.append(
                EditorialIssue(
                    code="ED015c",
                    severity="warning",
                    line=line_no,
                    message=f"Possível palavra repetida consecutiva: '{m_dup.group(0)}'.",
                    excerpt=m_dup.group(0),
                )
            )

    for m_hyph in re.finditer(r"([a-zà-ÿ]{2,})-\r?\n([a-zà-ÿ]{2,})", masked_body):
        line_no = masked_body[: m_hyph.start()].count("\n") + 1
        issues.append(
            EditorialIssue(
                code="ED015b",
                severity="error",
                line=line_no,
                message=f"Hifenização quebrada entre linhas ('{m_hyph.group(1)}-{m_hyph.group(2)}').",
                excerpt=f"{m_hyph.group(1)}- / {m_hyph.group(2)}",
            )
        )

    return issues


def _extract_metrics_from_markdown_text(raw_text: str) -> SourceMetrics:
    match = re.match(r"^---\r?\n[\s\S]*?\r?\n---\r?\n([\s\S]*)$", raw_text)
    body = match.group(1) if match else raw_text

    fn_defs = re.findall(r"^\[\^(\d+)\]:", body, re.MULTILINE)
    headings = len(re.findall(r"^#{1,6}\s+\S", body, re.MULTILINE))

    # Remove definições de notas e marcação markdown antes de contar palavras e parágrafos
    body_clean = re.sub(r"^\[\^[^\]]+\]:.*$", "", body, flags=re.MULTILINE)
    body_clean = re.sub(r"\[\^[^\]]+\]", "", body_clean)
    body_clean = re.sub(r"```[\s\S]*?```", "", body_clean)
    body_clean = re.sub(r"^#{1,6}\s+", "", body_clean, flags=re.MULTILINE)
    body_clean = re.sub(r"[*_`>]", " ", body_clean)

    paragraphs = len([blk for blk in re.split(r"\n\s*\n", body_clean) if blk.strip() and blk.strip() != "---"])
    words = len(re.findall(r"\b\w+\b", body_clean))
    return SourceMetrics(words=words, paragraphs=paragraphs, headings=headings, author_footnotes=len(set(fn_defs)))


def _extract_source_metrics(source_path: Path) -> tuple[SourceMetrics | None, list[EditorialIssue]]:
    suffix = source_path.suffix.lower()
    if suffix in (".md", ".txt"):
        text = source_path.read_text(encoding="utf-8", errors="replace")
        return _extract_metrics_from_markdown_text(text), []

    if suffix in (".html", ".htm"):
        raw = source_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()
        headings = len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))
        paragraphs = len([p for p in soup.find_all("p") if p.get_text(strip=True)])
        plain = soup.get_text(separator=" ")
        words = len(re.findall(r"\b\w+\b", plain))
        return SourceMetrics(words=words, paragraphs=paragraphs, headings=headings, author_footnotes=0), []

    if suffix == ".pdf":
        try:
            import fitz
        except ImportError:
            return None, [
                EditorialIssue(
                    code="SRC000",
                    severity="warning",
                    line=None,
                    message=(
                        "Extrator de PDF (PyMuPDF/fitz) não instalado neste ambiente; "
                        "para auditoria automática de fonte PDF use a matriz em data/draft/*.md."
                    ),
                )
            ]

        doc = fitz.open(str(source_path))
        try:
            text_pages = [page.get_text("text") for page in doc]
        finally:
            doc.close()
        full_text = "\n\n".join(text_pages)
        words = len(re.findall(r"\b\w+\b", full_text))
        paragraphs = len([blk for blk in re.split(r"\n\s*\n", full_text) if blk.strip()])
        return SourceMetrics(words=words, paragraphs=paragraphs, headings=0, author_footnotes=0), []

    return None, [
        EditorialIssue(
            code="SRC000",
            severity="warning",
            line=None,
            message=f"Formato de matriz '{suffix}' sem comparador automático suportado.",
        )
    ]


def compare_with_source(
    review_path: str | Path,
    source_path: str | Path,
    translated: bool = False,
) -> SourceComparisonReport:
    """Compara métricas estruturais do documento revisado contra a matriz local original."""
    rev_file = Path(review_path)
    src_file = Path(source_path)

    parsed_rev = parse_markdown_file(rev_file)
    rev_metrics = _extract_metrics_from_markdown_text(parsed_rev["body"])

    if not src_file.exists():
        return SourceComparisonReport(
            source_metrics=SourceMetrics(words=0, paragraphs=0, headings=0, author_footnotes=0),
            review_metrics=rev_metrics,
            word_ratio=0.0,
            issues=[
                EditorialIssue(
                    code="SRC000",
                    severity="error",
                    line=None,
                    message=f"Arquivo-fonte não encontrado: {src_file}",
                )
            ],
        )

    src_metrics, extract_issues = _extract_source_metrics(src_file)
    if src_metrics is None:
        return SourceComparisonReport(
            source_metrics=SourceMetrics(words=0, paragraphs=0, headings=0, author_footnotes=0),
            review_metrics=rev_metrics,
            word_ratio=0.0,
            issues=extract_issues,
        )

    ratio = rev_metrics.words / max(1, src_metrics.words)
    issues: list[EditorialIssue] = list(extract_issues)

    if src_metrics.words >= 50:
        min_ratio = 0.50 if translated else 0.65
        max_ratio = 1.80 if translated else 1.55
        if ratio < 0.50:
            issues.append(
                EditorialIssue(
                    code="SRC001",
                    severity="error",
                    line=None,
                    message=(
                        f"Queda severa de extensão frente à matriz (razão {ratio:.2f}: "
                        f"{rev_metrics.words} vs {src_metrics.words} palavras). Possível truncamento."
                    ),
                )
            )
        elif ratio < min_ratio or ratio > max_ratio:
            issues.append(
                EditorialIssue(
                    code="SRC001",
                    severity="warning",
                    line=None,
                    message=(
                        f"Desvio de extensão frente à matriz (razão {ratio:.2f}: "
                        f"{rev_metrics.words} vs {src_metrics.words} palavras)."
                    ),
                )
            )

    if src_metrics.author_footnotes > 0 and rev_metrics.author_footnotes < src_metrics.author_footnotes:
        issues.append(
            EditorialIssue(
                code="SRC002",
                severity="error",
                line=None,
                message=(
                    f"Perda de notas do autor: matriz possui {src_metrics.author_footnotes} nota(s) "
                    f"e revisão possui {rev_metrics.author_footnotes}."
                ),
            )
        )

    return SourceComparisonReport(
        source_metrics=src_metrics,
        review_metrics=rev_metrics,
        word_ratio=ratio,
        issues=issues,
    )


def _check_list_spacing(raw_lines: list[str]) -> list[EditorialIssue]:
    """Garante linha em branco acima de qualquer lista ou sublista (compatibilidade Leia-me)."""
    issues: list[EditorialIssue] = []
    body_start = 0
    if raw_lines and raw_lines[0].strip() == "---":
        for i in range(1, len(raw_lines)):
            if raw_lines[i].strip() == "---":
                body_start = i + 1
                break

    in_code = False
    for idx in range(body_start, len(raw_lines)):
        line = raw_lines[idx]
        stripped_left = line.lstrip()
        if stripped_left.startswith("```") or stripped_left.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or idx <= body_start:
            continue

        bq_match = _BQ_PREFIX_RE.match(line)
        cur_bq_prefix, cur_rest = bq_match.groups() if bq_match is not None else ("", line)
        m_cur = _LIST_ITEM_RE.match(cur_rest)
        if not m_cur:
            continue

        prev_raw = raw_lines[idx - 1]
        if prev_raw.strip() == "":
            continue

        prev_bq_match = _BQ_PREFIX_RE.match(prev_raw)
        prev_bq_prefix, prev_rest = prev_bq_match.groups() if prev_bq_match is not None else ("", prev_raw)
        cur_bq_depth = cur_bq_prefix.count(">")
        prev_bq_depth = prev_bq_prefix.count(">")
        if prev_bq_depth == cur_bq_depth and prev_rest.strip() == "":
            continue

        line_no = idx + 1
        if prev_bq_depth != cur_bq_depth:
            issues.append(
                EditorialIssue(
                    code="ED017",
                    severity="error",
                    line=line_no,
                    message="Lista sem linha em branco imediatamente acima (quebra a renderização no leitor Leia-me).",
                    excerpt=line.strip()[:80],
                )
            )
            continue

        m_prev = _LIST_ITEM_RE.match(prev_rest)
        if m_prev is None:
            issues.append(
                EditorialIssue(
                    code="ED017",
                    severity="error",
                    line=line_no,
                    message="Lista sem linha em branco imediatamente acima (quebra a renderização no leitor Leia-me).",
                    excerpt=line.strip()[:80],
                )
            )
            continue

        cur_indent = len(m_cur.group(1))
        cur_kind = "ul" if m_cur.group(2) else "ol"
        prev_indent = len(m_prev.group(1))
        prev_kind = "ul" if m_prev.group(2) else "ol"
        if cur_indent != prev_indent or cur_kind != prev_kind:
            issues.append(
                EditorialIssue(
                    code="ED017",
                    severity="error",
                    line=line_no,
                    message=(
                        "Sublista ou mudança de nível/tipo de lista sem linha em branco imediatamente acima "
                        "(quebra a renderização no leitor Leia-me)."
                    ),
                    excerpt=line.strip()[:80],
                )
            )

    return issues


def _extract_ignored_rules_by_line(raw_lines: list[str]) -> dict[int, set[str]]:
    """Extrai diretivas <!-- openscimd-ignore: CODIGO --> fora do frontmatter e de código."""
    ignored: dict[int, set[str]] = {}
    body_start = 0
    if raw_lines and raw_lines[0].strip() == "---":
        for i in range(1, len(raw_lines)):
            if raw_lines[i].strip() == "---":
                body_start = i + 1
                break

    fence_marker: str | None = None
    for idx in range(body_start, len(raw_lines)):
        line = raw_lines[idx]
        stripped_left = line.lstrip()
        if stripped_left.startswith("```") or stripped_left.startswith("~~~"):
            marker = stripped_left[:3]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue

        scan_line = re.sub(r"`+[^`\n]+`+", " ", line)
        matches = list(_IGNORE_DIRECTIVE_RE.finditer(scan_line))
        if not matches:
            continue

        codes: set[str] = set()
        for m in matches:
            for tok in re.split(r"[\s,]+", m.group(1).strip()):
                if tok:
                    codes.add(tok.lower())
        if not codes:
            continue

        remainder = _IGNORE_DIRECTIVE_RE.sub("", line).strip()
        if remainder:
            ignored.setdefault(idx + 1, set()).update(codes)
            continue

        target_idx = idx + 1
        while target_idx < len(raw_lines):
            cand = raw_lines[target_idx]
            cand_stripped = cand.strip()
            if not cand_stripped:
                target_idx += 1
                continue
            if cand_stripped.startswith("```") or cand_stripped.startswith("~~~"):
                break
            cand_scan = re.sub(r"`+[^`\n]+`+", " ", cand)
            if _IGNORE_DIRECTIVE_RE.search(cand_scan) and not _IGNORE_DIRECTIVE_RE.sub("", cand).strip():
                target_idx += 1
                continue
            ignored.setdefault(target_idx + 1, set()).update(codes)
            break

    return ignored


def lint_markdown_text(
    raw_text: str,
    file_path: str | Path = Path("<memory>"),
) -> LintReport:
    """Executa todas as regras do linter editorial sobre uma string Markdown."""
    raw_lines = raw_text.splitlines()
    masked_with_fn = _mask_non_prose(raw_text, keep_footnotes=True)
    masked_prose = _mask_non_prose(raw_text, keep_footnotes=False)

    masked_with_fn_lines = masked_with_fn.splitlines()
    masked_prose_lines = masked_prose.splitlines()
    notes_start_line = _find_notes_start_line(masked_with_fn_lines)
    ignored_by_line = _extract_ignored_rules_by_line(raw_lines)

    issues: list[EditorialIssue] = []
    issues.extend(_check_headings(masked_prose_lines, notes_start_line=notes_start_line))
    issues.extend(_check_footnotes(masked_with_fn_lines))
    issues.extend(_check_typography_and_ocr(masked_prose_lines, masked_prose))
    issues.extend(_check_list_spacing(raw_lines))

    if ignored_by_line:
        issues = [
            issue
            for issue in issues
            if issue.line is None or issue.code.lower() not in ignored_by_line.get(issue.line, set())
        ]

    issues.sort(key=lambda item: (item.line if item.line is not None else 999_999, item.code))
    return LintReport(file_path=Path(file_path), issues=issues)


def lint_markdown_file(
    file_path: str | Path,
    source_path: str | Path | None = None,
    translated: bool = False,
) -> LintReport:
    """Lê um arquivo Markdown e executa o linter editorial (e comparação opcional contra matriz)."""
    target = Path(file_path)
    raw_text = target.read_text(encoding="utf-8")
    report = lint_markdown_text(raw_text, file_path=target)

    if source_path is not None:
        comparison = compare_with_source(target, source_path, translated=translated)
        return LintReport(file_path=target, issues=report.issues, comparison=comparison)
    return report
