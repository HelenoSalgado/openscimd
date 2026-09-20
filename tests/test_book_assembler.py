"""Testes unitários para o montador de volumes BookAssembler."""

from pathlib import Path
import pytest
import yaml
from scripts.book_assembler import BookAssembler


def test_shift_headings():
    text = "# Título 1\n## Título 2\n### Título 3\nParágrafo normal."
    shifted = BookAssembler.shift_headings(text, level_offset=1)
    assert "## Título 1" in shifted
    assert "### Título 2" in shifted
    assert "#### Título 3" in shifted
    assert "Parágrafo normal." in shifted


def test_extract_notes_from_body():
    body = (
        "Texto do tratado com nota de rodapé[^1].\n\n"
        "---\n\n"
        "### Notas do Autor\n\n"
        "[^1]: Referência à edição crítica."
    )
    clean_body, notes = BookAssembler.extract_notes_from_body(body)
    assert "Texto do tratado com nota de rodapé[^1]." in clean_body
    assert "[^1]: Referência à edição crítica." in notes
    assert "### Notas do Autor" not in clean_body


def test_assemble_volume_end_to_end(tmp_path: Path):
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()

    part1 = parts_dir / "01-primeira-parte.md"
    part1.write_text(
        "---\n"
        'title: "A Palavra de Deus"\n'
        'author: "Hugo de São Vítor"\n'
        "---\n\n"
        "## Capítulo I\n\n"
        "Uma só vez falou Deus.\n",
        encoding="utf-8",
    )

    part2 = parts_dir / "02-segunda-parte.md"
    part2.write_text(
        "---\n"
        'title: "A Substância do Amor"\n'
        'author: "Hugo de São Vítor"\n'
        "---\n\n"
        "## Capítulo Único\n\n"
        "O amor é fonte de todos os bens.[^1]\n\n"
        "---\n\n"
        "[^1]: Citação clássica.\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "volume_completo.md"
    metadata = {
        "title": "Opúsculos Espirituais e Teológicos",
        "authors": [{"name": "Hugo de São Vítor"}],
        "summary": "Resumo dos opúsculos.",
        "date": "c. 1130 d.C.",
        "license": "CC BY-NC 4.0",
        "categories": ["Teologia", "Mística"],
    }

    result = BookAssembler.assemble_volume(parts_dir, output_file, metadata)
    assert result.exists()

    content = result.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "title: Opúsculos Espirituais e Teológicos" in content
    assert "## *A Palavra de Deus*[^ne1][^ne2][^ne3]" in content
    assert "### Capítulo I" in content
    assert "## *A Substância do Amor*" in content
    assert "### Capítulo Único" in content
    assert "### Notas Editoriais" in content
    assert "### Notas do Autor" in content
    assert "[^1]: Citação clássica." in content
