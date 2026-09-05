"""Unit tests for the spellchecker and archaic review system."""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from main import app
from scripts.spellchecker import (
    ArchaicMatcher,
    CasePreserver,
    DictionaryManager,
    HunspellClient,
    MarkdownMasker,
    ReviewEngine,
    review_path,
)
from scripts.spellchecker.definition_lookup import DefinitionLookup

runner = CliRunner()


def test_dictionary_sanitization_removes_identities():
    raw_dict = {
        "homem": "homem",
        "hesitar": "hesitar",
        "Activo": "ativo",
        "d'elle": "dele",
        "   ": "vazio",
        "val": "  ",
    }
    sanitized = DictionaryManager.sanitize_entries(raw_dict)
    assert "homem" not in sanitized
    assert "hesitar" not in sanitized
    assert sanitized["activo"] == "ativo"
    assert sanitized["d'elle"] == "dele"
    assert len(sanitized) == 2


def test_dictionary_ignored_words(tmp_path):
    ign_file = tmp_path / "ignored.json"
    dm = DictionaryManager(ignored_path=ign_file)
    assert not dm.is_ignored("burrus")

    dm.add_ignored("Burrus")
    assert dm.is_ignored("burrus")
    assert dm.is_ignored("BURRUS")

    # Reload from disk
    dm2 = DictionaryManager(ignored_path=ign_file)
    assert dm2.is_ignored("burrus")


def test_case_preserver():
    # UPPERCASE
    assert CasePreserver.preserve_case("ACTIVO", "ativo") == "ATIVO"
    assert CasePreserver.preserve_case("VOSSA MERCÊ", "você") == "VOCÊ"

    # TitleCase / Capitalized
    assert CasePreserver.preserve_case("Activo", "ativo") == "Ativo"
    assert CasePreserver.preserve_case("Vossa MercÊ", "você") == "Você"
    assert CasePreserver.preserve_case("Vossa mercê", "você") == "Você"

    # Lowercase
    assert CasePreserver.preserve_case("activo", "ativo") == "ativo"
    assert CasePreserver.preserve_case("vossa mercê", "você") == "você"


def test_markdown_masker_preserves_length_and_lines():
    sample = """---
title: Test Title
author: Nam
---
# Header

Texto normal com `código nam` e [link](https://nam.com) e $$x = 1$$ e <!-- nam -->.
Mais texto com nam.
"""
    masked = MarkdownMasker.mask(sample)
    assert len(masked) == len(sample)
    assert masked.count("\n") == sample.count("\n")

    # Frontmatter masked
    assert "title: Test Title" not in masked
    # Code block masked
    assert "código nam" not in masked
    # Link url masked
    assert "https://nam.com" not in masked
    # Link text preserved
    assert "link" in masked
    # Plain text preserved
    assert "Texto normal com" in masked
    assert "Mais texto com nam." in masked


def test_archaic_matcher_ignores_identities_and_finds_phrases():
    dictionary = {
        "homem": "homem",  # Identity (should be ignored)
        "vossa mercê": "você",
        "baptismo": "batismo",
        "d'elle": "dele",
    }
    matcher = ArchaicMatcher(dictionary, ignored_words={"d'elle"})
    text = "O homem disse: Vossa Mercê deseja o baptismo d'elle?"

    matches = matcher.find_matches(text, mask_markdown=False, use_hunspell=False)

    assert len(matches) == 2
    # homem should NOT be in matches
    assert not any(m.dict_key == "homem" for m in matches)
    # d'elle is ignored
    assert not any(m.dict_key == "d'elle" for m in matches)

    assert matches[0].dict_key == "vossa mercê"
    assert matches[0].original_text == "Vossa Mercê"
    assert matches[0].suggested_text == "Você"

    assert matches[1].dict_key == "baptismo"
    assert matches[1].original_text == "baptismo"
    assert matches[1].suggested_text == "batismo"


def test_hunspell_client():
    client = HunspellClient("pt_BR")
    if client.is_available:
        valid, _ = client.check_word("homem")
        assert valid is True

        valid, suggs = client.check_word("baptismo")
        assert valid is False
        assert "batismo" in suggs or "bautismo" in suggs


def test_definition_lookup_cache(tmp_path):
    cache_file = tmp_path / "defs.json"
    dl = DefinitionLookup(cache_file=cache_file)
    dl._cache["zelo"] = {
        "word": "zelo",
        "class": "substantivo masculino",
        "meaning": "Cuidado ou atenção excessiva.",
        "etymology": "",
        "notes": "",
    }
    dl._save_cache()

    dl2 = DefinitionLookup(cache_file=cache_file)
    entry = dl2.get_definition("zelo")
    assert entry is not None
    assert entry["word"] == "zelo"
    assert "Cuidado" in entry["meaning"]


def test_review_engine_apply_replacements():
    content = "A acção e o baptismo foram realizados."
    # Matches: acção (start 2, end 7) -> ação, baptismo (start 12, end 20) -> batismo
    replacements = [
        (2, 7, "ação"),
        (12, 20, "batismo"),
    ]
    result = ReviewEngine.apply_replacements(content, replacements)
    assert result == "A ação e o batismo foram realizados."


def test_cli_review_dry_run(tmp_path):
    md_file = tmp_path / "artigo.md"
    md_file.write_text("# Artigo\n\nA acção do homem e o baptismo.\n", encoding="utf-8")

    result = runner.invoke(app, ["review", str(md_file), "--check", "--no-hunspell"])
    assert result.exit_code == 0
    # acção and baptismo detected from dictionary (2 matches), homem is NOT an archaism
    assert "2 arcaísmos/erros encontrados" in result.stdout
    # Detailed report listing detected words
    assert "Dicionário Curado" in result.stdout
    assert "acção" in result.stdout
    assert "ação" in result.stdout
    assert "baptismo" in result.stdout
    assert "batismo" in result.stdout
    # Original file unchanged
    assert "acção" in md_file.read_text(encoding="utf-8")


def test_format_dry_run_report(tmp_path):
    from scripts.spellchecker import format_dry_run_report
    from scripts.spellchecker.models import FileReviewResult, ReviewMatch

    empty_res = FileReviewResult(filepath=tmp_path / "empty.md", total_found=0)
    assert "0 arcaísmos/erros encontrados" in format_dry_run_report(empty_res)
    assert "✅" in format_dry_run_report(empty_res)

    match_dict = ReviewMatch(
        start=0,
        end=5,
        original_text="acção",
        suggested_text="ação",
        dict_key="acção",
        line_number=3,
        column_number=1,
        line_content="acção",
        source="dictionary",
    )
    match_hunspell = ReviewMatch(
        start=10,
        end=18,
        original_text="Magister",
        suggested_text="Magistro",
        dict_key="magister",
        line_number=5,
        column_number=1,
        line_content="Magister",
        source="hunspell",
        suggestions=["Magistro", "Mestre"],
    )

    res = FileReviewResult(
        filepath=tmp_path / "teste.md",
        total_found=2,
        matches=[match_dict, match_hunspell],
    )
    report = format_dry_run_report(res)
    assert "2 arcaísmos/erros encontrados" in report
    assert "Dicionário Curado" in report
    assert "acção" in report
    assert "ação" in report
    assert "Hunspell / Não Reconhecidas ou Estrangeiras" in report
    assert "Magister" in report
    assert "Magistro" in report


def test_cli_review_auto_apply_with_output_preservation(tmp_path):
    src_file = tmp_path / "original.md"
    out_file = tmp_path / "revisado.md"
    src_file.write_text("# Artigo\n\nA acção do homem e o baptismo.\n", encoding="utf-8")

    result = runner.invoke(app, ["review", str(src_file), "-o", str(out_file), "--auto-fix", "--no-hunspell"])
    assert result.exit_code == 0
    assert "2 substituições aplicadas automaticamente" in result.stdout

    # Original file is preserved untouched
    assert "A acção do homem e o baptismo." in src_file.read_text(encoding="utf-8")

    # Output file has the corrections
    assert out_file.exists()
    assert "A ação do homem e o batismo." in out_file.read_text(encoding="utf-8")
