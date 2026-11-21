"""Testes unitários para o linter editorial determinístico e comparador de matriz."""

from __future__ import annotations

from pathlib import Path

from scripts.editorial_linter import compare_with_source, lint_markdown_file, lint_markdown_text


def _valid_doc(body: str) -> str:
    return (
        "---\n"
        'title: "Estudo de Caso Editorial"\n'
        'author: "Autor Teste"\n'
        'summary: "Resumo"\n'
        'date: "2026-06-20"\n'
        'license: "CC BY 4.0"\n'
        'language: "pt-BR"\n'
        "categories:\n"
        "  - Filosofia\n"
        "---\n\n"
        f"{body}\n"
    )


def test_lint_accepts_valid_editorial_document() -> None:
    doc = _valid_doc(
        "## Introdução[^ne1]\n\n"
        "### Capítulo IV\n\n"
        "## VIII\n\n"
        "## Modelos LLMs e IA\n\n"
        "O autor escreveu “palavras sábias” e «máxima clássica» entre 1510–1562[^1].\n"
        "Veja também a referência canônica Jo 1.1–14, etc.[^nt1]\n\n"
        "---\n\n"
        "### Notas Editoriais\n\n"
        "[^ne1]: Nota editorial.\n\n"
        "### Notas do Tradutor\n\n"
        "[^nt1]: **N. do T.**: Esclarecimento filológico.\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Referência original."
    )
    report = lint_markdown_text(doc)
    assert report.is_valid
    assert report.errors == []
    assert report.warnings == []


def test_lint_headings_rules_ed001_to_ed004() -> None:
    doc = _valid_doc(
        "# Título Indevido\n\n"
        "## **Negrito Proibido**\n\n"
        "### QUESTÃO SEXTA\n\n"
        "##### Salto Excessivo\n\n"
        "Texto normal."
    )
    report = lint_markdown_text(doc)
    codes = {issue.code for issue in report.all_issues}
    assert {"ED001", "ED002", "ED003", "ED004"}.issubset(codes)


def test_lint_quotes_straight_rejected_outside_code_and_yaml() -> None:
    doc = _valid_doc(
        'Texto com "aspas retas" no parágrafo.\n\n'
        "```python\n"
        'x = "permitido em código"\n'
        "```"
    )
    report = lint_markdown_text(doc)
    ed005 = [issue for issue in report.errors if issue.code == "ED005"]
    assert len(ed005) == 1
    assert "aspas retas" in ed005[0].excerpt


def test_lint_footnotes_abnt_and_sequence_rules() -> None:
    doc = _valid_doc(
        "## Seção[^ne2]\n\n"
        "Texto com espaço [^1] e ponto antes.[^2]\n\n"
        "Âncora sem definição[^3].\n\n"
        "---\n\n"
        "### Notas Editoriais\n\n"
        "[^ne2]: Quebra de sequência sem ne1.\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Primeira nota.\n"
        "[^2]: Segunda nota sem linha em branco acima.\n\n"
        "[^9]: Nota órfã."
    )
    report = lint_markdown_text(doc)
    codes = {issue.code for issue in report.errors}
    assert {"ED006", "ED007", "ED008", "ED009", "ED010", "ED011"}.issubset(codes)


def test_lint_abnt_allows_abbreviation_dot_before_anchor() -> None:
    doc = _valid_doc(
        "## Introdução\n\n"
        "Platão, Aristóteles, etc.[^1] E em 399 a.C.[^2] nos textos do N.T.[^3]\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Nota sobre abreviação.\n\n"
        "[^2]: Nota sobre era.\n\n"
        "[^3]: Nota sobre sigla."
    )
    report = lint_markdown_text(doc)
    assert not any(issue.code == "ED010" for issue in report.all_issues)


def test_lint_ed012_allows_hr_before_bibliography_but_rejects_between_note_sections() -> None:
    doc_with_bib = _valid_doc(
        "## Introdução\n\n"
        "Texto com nota[^1] e nota do tradutor[^nt1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Nota do autor.\n\n"
        "### Notas do Tradutor\n\n"
        "[^nt1]: Nota do tradutor.\n\n"
        "---\n\n"
        "## Bibliografia\n\n"
        "- **Autor**, 2020, *Obra*."
    )
    report_bib = lint_markdown_text(doc_with_bib)
    assert not any(issue.code == "ED012" for issue in report_bib.all_issues)

    doc_with_inner_hr = _valid_doc(
        "## Introdução\n\n"
        "Texto com nota[^1] e nota do tradutor[^nt1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Nota do autor.\n\n"
        "---\n\n"
        "### Notas do Tradutor\n\n"
        "[^nt1]: Nota do tradutor."
    )
    report_inner = lint_markdown_text(doc_with_inner_hr)
    assert any(issue.code == "ED012" for issue in report_inner.all_issues)


def test_lint_numeric_ranges_ignores_dates_urls_dois_and_numbered_paragraphs() -> None:
    doc = _valid_doc(
        "## Seção\n\n"
        "2 - Parágrafo numerado em 2026-11-20 com DOI 10.5281/zenodo.1234-5678 "
        "e ISSN 1982-5587 em [link](https://example.com/1-2).\n\n"
        "Mas o intervalo 1510-1562 e Jo 1.1-14 devem ser rejeitados."
    )
    report = lint_markdown_text(doc)
    ed013 = [issue for issue in report.errors if issue.code == "ED013"]
    assert len(ed013) == 1
    assert "1510-1562" in ed013[0].excerpt or "1-14" in ed013[0].excerpt


def test_lint_biblical_bad_separator_without_false_positives() -> None:
    doc = _valid_doc(
        "## Seção\n\n"
        "Aqui temos os 10, 20 motivos, por ex. 1, 2 casos, na 3, 4 partes.\n\n"
        "Formas válidas: Jo 3.16, João 3.16, Hb 11.1, Hebreus 11.1, 1Co 15.3–4, "
        "1 Coríntios 15.3–4, Salmo 23.1, A Segunda Carta aos Coríntios 2.1.\n\n"
        "Formas inválidas: Jo 3:16, Salmo 61, 12, HB 11.1, Mat. 5.3, 1 Co 10.13, "
        "I Coríntios 10.13, 1Coríntios 10.13 e A Segunda Carta aos Coríntios 2:1."
    )
    report = lint_markdown_text(doc)
    ed014 = [issue for issue in report.errors if issue.code == "ED014"]
    messages = "\n".join(issue.message for issue in ed014)
    assert len(ed014) == 8
    assert "Jo 3:16" in messages
    assert "HB 11.1" in messages
    assert "Hb 11.1" in messages
    assert "Mat. 5.3" in messages
    assert "Mt 5.3" in messages
    assert "1 Co 10.13" in messages
    assert "1Co 10.13" in messages
    assert "I Coríntios 10.13" in messages
    assert "1 Coríntios 10.13" in messages
    assert "Segunda Carta aos Coríntios 2:1" in messages
    assert "os 10, 20" not in messages
    assert "por ex. 1, 2" not in messages


def test_lint_biblical_chained_aliases_interchapter_and_no_false_positives() -> None:
    doc = _valid_doc(
        "## Seção\n\n"
        "Erros: (Êx 34:7), 1Cro. 16:15, Mc.10:34, Salmos 81.3 e 92:4, "
        "Romanos 1.11; 7:14; 15:27, Mc 2.18–3:6, Salmos 19:13b.\n\n"
        "Válidos: proporção de 2:1, Works, 2:31, Salmos 139.1–4, 23, 1 João 5.7–8, 99%, "
        "(números 2, 11, 12 e 13), (ver números 10, 17, 23), nos atos 1, 2 e 3, "
        "em Lucas 1, 10 e 20, em Lucas 1, 10, e 20 e capítulos de Mateus 1, 2, 3."
    )
    report = lint_markdown_text(doc)
    ed014 = [issue for issue in report.errors if issue.code == "ED014"]
    messages = "\n".join(issue.message for issue in ed014)
    assert len(ed014) == 8
    for expected_bad in ("Êx 34:7", "1Cro. 16:15", "Mc.10:34", "92:4", "7:14", "15:27", "Mc 2.18–3:6", "Salmos 19:13b"):
        assert expected_bad in messages
    for non_bible in ("2:1", "2:31", "139.1", "99", "números", "atos", "Lucas", "Mateus"):
        assert non_bible not in messages


def test_lint_ocr_and_duplicate_words() -> None:
    doc = _valid_doc(
        "## Seção\n\n"
        "O m0do incorreto de transcrever pala-\nvra partida e os erros erros repetidos."
    )
    report = lint_markdown_text(doc)
    codes = {issue.code for issue in report.all_issues}
    assert {"ED015a", "ED015b", "ED015c"}.issubset(codes)


def test_compare_with_source_detects_truncation_and_missing_notes(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "---\ntitle: Original\n---\n\n"
        + ("Palavra exemplo de prosa acadêmica densa com argumentos completos. " * 25)
        + "Nota[^1] e nota[^2].\n\n---\n\n[^1]: Nota um.\n\n[^2]: Nota dois.\n",
        encoding="utf-8",
    )

    review = tmp_path / "review.md"
    review.write_text(
        _valid_doc("## Introdução\n\nResumo muito curto que cortou quase todo o texto[^1].\n\n---\n\n### Notas do Autor\n\n[^1]: Nota um."),
        encoding="utf-8",
    )

    comp = compare_with_source(review, source)
    assert comp.word_ratio < 0.50
    codes = {issue.code for issue in comp.issues}
    assert "SRC001" in codes
    assert "SRC002" in codes

    full_report = lint_markdown_file(review, source_path=source)
    assert not full_report.is_valid
