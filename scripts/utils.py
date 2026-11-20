from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

_PT_MONTHS: dict[str, int] = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "março": 3,
    "abr": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
}


def parse_date_to_timestamp(date_str: Any) -> int | None:
    """Converte data ISO, DD-MM-YYYY ou padrão ABNT brasileiro para timestamp Unix em ms."""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        dt = date_str if date_str.tzinfo else date_str.replace(tzinfo=UTC)
        return int(dt.timestamp() * 1000)
    if isinstance(date_str, date):
        return int(datetime(date_str.year, date_str.month, date_str.day, tzinfo=UTC).timestamp() * 1000)

    raw = str(date_str).strip()
    if not raw:
        return None

    # DD-MM-YYYY ou DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if month > 12 and day <= 12:
            day, month = month, day
        try:
            return int(datetime(year, month, day, tzinfo=UTC).timestamp() * 1000)
        except ValueError:
            return None

    # YYYY-MM-DD ou YYYY/MM/DD
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", raw)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return int(datetime(year, month, day, tzinfo=UTC).timestamp() * 1000)
        except ValueError:
            return None

    # Padrão ABNT brasileiro: "20 nov. 2025" ou "20 de novembro de 2025" / "1º de janeiro de 2026"
    m_abnt = re.match(
        r"^(\d{1,2})[º°]?\s+(?:de\s+)?([a-zA-ZçÇ]{3,10})\.?\s+(?:de\s+)?(\d{4})$",
        raw,
    )
    if m_abnt:
        day = int(m_abnt.group(1))
        month_key = m_abnt.group(2).lower()
        year = int(m_abnt.group(3))
        month_num = _PT_MONTHS.get(month_key)
        if month_num is not None:
            try:
                return int(datetime(year, month_num, day, tzinfo=UTC).timestamp() * 1000)
            except ValueError:
                return None

    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def estimate_reading_time(body: str, wpm: int = 200) -> int:
    """Estima o tempo de leitura em minutos a partir da contagem de palavras do corpo."""
    text = re.sub(r"```[\s\S]*?```", "", body)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#*_\-~\[\]()]", " ", text)
    words = len([w for w in text.split() if w.strip()])
    return max(1, (words + wpm - 1) // wpm)


def parse_markdown_file(file_path: str | Path) -> dict[str, Any]:
    """Lê um arquivo Markdown e separa Frontmatter YAML e corpo."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$", content)
    if not match:
        return {"metadata": {}, "body": content}

    yaml_str = match.group(1)
    body = match.group(2)

    try:
        loaded = yaml.safe_load(yaml_str) or {}
        metadata: dict[str, Any] = loaded if isinstance(loaded, dict) else {}
    except yaml.YAMLError:
        metadata = {}

    return {"metadata": metadata, "body": body}


def is_draft(metadata: dict[str, Any]) -> bool:
    """Retorna True se os metadados indicam rascunho não publicável."""
    draft = metadata.get("draft")
    status = metadata.get("status")
    return draft is True or str(draft).lower() == "true" or status == "draft"


def remove_empty_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Remove chaves cujo valor seja None, string vazia ou lista vazia."""
    clean: dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        if isinstance(v, list) and not v:
            continue
        clean[k] = v
    return clean


def slugify(text: str | None) -> str:
    """Normaliza uma string para slug kebab-case ASCII."""
    if not text:
        return "geral"
    norm = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower().strip()
    norm = re.sub(r"[\(].*?[\)]", "", norm)
    norm = re.sub(r"[^\w\s-]", "", norm)
    norm = re.sub(r"[\s_]+", "-", norm)
    return norm.strip("-") or "geral"


def get_files_recursively(directory: str | Path, extension: str = ".md") -> list[str]:
    """Lista recursivamente arquivos com a extensão dada (ignorando manifestos .audit.md)."""
    results: list[str] = []
    path = Path(directory)
    if not path.exists():
        return results
    for p in sorted(path.rglob(f"*{extension}")):
        if p.is_file() and not p.name.endswith(".audit.md"):
            results.append(str(p))
    return results
