import shutil
from pathlib import Path
import pytest
from typer.testing import CliRunner

from main import app
from scripts.md2print import (
    calculate_kdp_spine_width_mm,
    convert_md_to_print_interior,
    generate_print_cover_spread,
    get_pdf_page_count,
)

runner = CliRunner()


def test_calculate_kdp_spine_width():
    # 80 páginas em papel creme (0.0572 mm/pág)
    spine_cream = calculate_kdp_spine_width_mm(80, paper_type="cream")
    assert spine_cream == round(80 * 0.0572, 2)

    # 81 páginas (deve arredondar para 82 páginas no cálculo de papel frente/verso)
    spine_cream_odd = calculate_kdp_spine_width_mm(81, paper_type="cream")
    assert spine_cream_odd == round(82 * 0.0572, 2)

    # 100 páginas em papel branco (0.05 mm/pág)
    spine_white = calculate_kdp_spine_width_mm(100, paper_type="white")
    assert spine_white == round(100 * 0.05, 2)

    # Valor mínimo de segurança
    assert calculate_kdp_spine_width_mm(2) >= 1.0


def test_get_pdf_page_count_real():
    interior_pdf = Path("dist/content/books/platao/apologia-de-socrates-interior.pdf")
    if not interior_pdf.exists():
        pytest.skip("PDF da Apologia não gerado ainda.")

    pages = get_pdf_page_count(interior_pdf)
    assert pages > 0
    assert pages in (36, 37, 38, 39, 40, 41, 42)


@pytest.mark.skipif(not shutil.which("pandoc"), reason="O executável 'pandoc' não está instalado no sistema operacional.")
def test_convert_md_to_print_interior_and_cover(tmp_path: Path):
    project_root = tmp_path
    (project_root / "pyproject.toml").write_text("[project]\nname='test'")
    
    # Template
    tpl_dir = project_root / "scripts" / "templates"
    tpl_dir.mkdir(parents=True)
    real_tpl = Path("scripts/templates/book_print.typ").read_text(encoding="utf-8")
    (tpl_dir / "book_print.typ").write_text(real_tpl, encoding="utf-8")

    # Livro
    book_file = project_root / "content" / "books" / "autor" / "obra.md"
    book_file.parent.mkdir(parents=True)
    book_file.write_text(
        """---
title: "Tratado Clássico"
author: "Pensador"
date: "IV a.C."
categories:
  - Filosofia
summary: "Um resumo editorial para teste."
---

## Primeiro Discurso

Abertura da dialética filosófica com nota de rodapé[^1].

[^1]: Nota de rodapé na mesma página.

### Seção Dialética

Desenvolvimento do pensamento e da justiça.
""",
        encoding="utf-8",
    )

    # Capa
    cover_dir = project_root / "assets" / "covers" / "originals"
    cover_dir.mkdir(parents=True)
    cover_img = cover_dir / "obra.png"
    # Copiar uma imagem PNG válida
    real_cover = Path("assets/covers/originals/apologia-de-socrates.png")
    if real_cover.exists():
        cover_img.write_bytes(real_cover.read_bytes())
    else:
        from PIL import Image
        im = Image.new("RGB", (400, 600), color="blue")
        im.save(str(cover_img), format="PNG")

    # Compilar Miolo
    out_interior = project_root / "dist" / "obra-interior.pdf"
    res_interior = convert_md_to_print_interior(
        input_md_path=book_file,
        output_pdf_path=out_interior,
        base_dir=project_root,
    )
    assert res_interior.exists()
    assert res_interior.stat().st_size > 0
    pages = get_pdf_page_count(res_interior)
    assert pages >= 4

    # Compilar Capa Aberta
    out_cover = project_root / "dist" / "obra-cover-spread.pdf"
    res_cover = generate_print_cover_spread(
        input_md_path=book_file,
        interior_pdf_path=res_interior,
        output_cover_pdf_path=out_cover,
        cover_image_path=cover_img,
        base_dir=project_root,
    )
    assert res_cover.exists()
    assert res_cover.stat().st_size > 0


def test_cli_build_print_validation():
    # Sem argumentos nem --all deve falhar com aviso claro
    res = runner.invoke(app, ["build-print"])
    assert res.exit_code == 1
    assert "Forneça o arquivo Markdown do livro ou use a flag '--all'" in res.stdout


def test_book_print_typ_gestalt_heading_proximity():
    """Garante rigorosa proximidade gestaltiana nos títulos e subtítulos impressos."""
    tpl_path = Path("scripts/templates/book_print.typ")
    assert tpl_path.exists()
    content = tpl_path.read_text(encoding="utf-8")

    # Controle de estado para detectar se subtítulo segue H1 ou parágrafo
    assert 'state("after-h1", false)' in content
    # Espaçamento de H2 em meio ao texto: proporção equilibrada (above 1.75em, below 1.35em)
    assert "block(above: 1.75em, below: 1.35em)" in content
    # Transição harmônica entre H1 e H2 quando consecutivos
    assert "block(above: 1.2em, below: 1.35em)" in content


def test_book_print_typ_titlepage_and_cip_centering():
    """Garante que a folha de rosto é puramente tipográfica e o quadro editorial é objetivo e não-redundante."""
    tpl_path = Path("scripts/templates/book_print.typ")
    assert tpl_path.exists()
    content = tpl_path.read_text(encoding="utf-8")

    # Folha de rosto centralizada na vertical e horizontal com pura tipografia (sem traços/losangos)
    assert "align(center + horizon)" in content
    assert "◆" not in content

    # Registro editorial objetivo, sem repetições burocráticas e com contagem exata para fins acadêmicos
    assert "REGISTRO EDITORIAL" in content
    assert "counter(page).final().first()" in content
    assert "width: 84%" in content
    assert "*Licença:* #license" in content

    # Tipografia ampliada e respiro para notas de rodapé
    assert "size: 12pt" in content
    assert "bottom: 16mm" in content
    assert "clearance: 2.2em" in content

    # Supressão de cabeçalho em páginas de abertura de capítulo
    assert "is-h1-page" in content


