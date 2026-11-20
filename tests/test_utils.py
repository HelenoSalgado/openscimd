"""Testes unitários para scripts/utils.py."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.utils import (
    estimate_reading_time,
    get_files_recursively,
    is_draft,
    parse_date_to_timestamp,
    parse_markdown_file,
    remove_empty_keys,
    slugify,
)


def test_parse_date_to_timestamp_iso_dmy_and_abnt() -> None:
    expected_nov20 = int(datetime(2025, 11, 20, tzinfo=UTC).timestamp() * 1000)
    assert parse_date_to_timestamp("2025-11-20") == expected_nov20
    assert parse_date_to_timestamp("20-11-2025") == expected_nov20
    assert parse_date_to_timestamp("20/11/2025") == expected_nov20
    assert parse_date_to_timestamp("20 nov. 2025") == expected_nov20
    assert parse_date_to_timestamp("20 de novembro de 2025") == expected_nov20

    expected_may1 = int(datetime(2024, 5, 1, tzinfo=UTC).timestamp() * 1000)
    assert parse_date_to_timestamp("1º de maio de 2024") == expected_may1

    assert parse_date_to_timestamp("399 a.C.") is None
    assert parse_date_to_timestamp("") is None
    assert parse_date_to_timestamp(None) is None


def test_parse_markdown_file_and_helpers(tmp_path: Path) -> None:
    md = tmp_path / "obra.md"
    md.write_text("---\ntitle: Teste\ndraft: true\n---\n\nTexto aqui.\n", encoding="utf-8")
    (tmp_path / "obra.audit.md").write_text("# Audit", encoding="utf-8")

    parsed = parse_markdown_file(md)
    assert parsed["metadata"]["title"] == "Teste"
    assert "Texto aqui." in parsed["body"]
    assert is_draft(parsed["metadata"]) is True

    files = get_files_recursively(tmp_path)
    assert len(files) == 1
    assert files[0].endswith("obra.md")

    assert estimate_reading_time("palavra " * 400, wpm=200) == 2
    assert remove_empty_keys({"a": 1, "b": "", "c": None, "d": []}) == {"a": 1}
    assert slugify("Peitho / Examina Antiqua (2011)") == "peitho-examina-antiqua"
