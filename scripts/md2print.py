#!/usr/bin/env python3
"""Compilador Editorial para Livros Impressos sob Demanda (Amazon KDP Print).

Gera arquivos PDF fixos de alta precisão tipográfica para miolo (14x21 cm) e
capa aberta (wrap-around cover com cálculo dinâmico de lombada) usando Typst.
"""

import math
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typst
import yaml

from scripts.md2epub import (
    extract_frontmatter,
    find_cover_image,
    format_editorial_date,
    resolve_author_name,
    resolve_epub_output_path,
)


def get_pdf_page_count(pdf_path: Path | str) -> int:
    """Extrai com precisão a contagem total de páginas de um arquivo PDF."""
    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

    # Método 1: pdfinfo (rápido e padrão no Arch Linux)
    if shutil.which("pdfinfo"):
        try:
            proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True)
            for line in proc.stdout.splitlines():
                if line.startswith("Pages:"):
                    return int(line.split(":")[1].strip())
        except Exception:
            pass

    # Método 2: Inspeção binária de objetos /Type /Page
    try:
        data = path.read_bytes()
        pages = re.findall(rb"/Type\s*/Page\b", data)
        if pages:
            return len(pages)
    except Exception:
        pass

    return 1


def calculate_kdp_spine_width_mm(page_count: int, paper_type: str = "cream") -> float:
    """Calcula a largura da lombada em milímetros segundo as fórmulas oficiais do Amazon KDP.
    
    - Papel creme (padrão literatura/filosofia): 0.0572 mm por página
    - Papel branco: 0.0500 mm por página
    """
    # A gráfica do KDP sempre arredonda o miolo para o número par seguinte (frente e verso)
    effective_pages = page_count if page_count % 2 == 0 else page_count + 1
    multiplier = 0.0572 if paper_type == "cream" else 0.0500
    width = round(effective_pages * multiplier, 2)
    # Lombada mínima para impressão de texto na lombada no KDP é de aproximadamente 79 páginas (~4.5 mm)
    return max(width, 1.0)


def convert_md_to_print_interior(
    input_md_path: str | Path,
    output_pdf_path: Optional[str | Path] = None,
    base_dir: Optional[str | Path] = None,
    trim_size: str = "14x21",
) -> Path:
    """Compila o miolo do livro em PDF diagramado em 14x21 cm com Typst."""
    input_path = Path(input_md_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {input_path}")

    project_root = Path(base_dir).resolve() if base_dir else input_path.parent
    while project_root != project_root.parent and not (project_root / "pyproject.toml").exists():
        project_root = project_root.parent

    if output_pdf_path:
        out_path = Path(output_pdf_path).resolve()
    else:
        content_dir = project_root / "content"
        if input_path.is_relative_to(content_dir):
            rel = input_path.relative_to(content_dir)
            out_path = project_root / "dist" / "content" / rel.with_name(f"{input_path.stem}-interior.pdf")
        else:
            out_path = project_root / "dist" / f"{input_path.stem}-interior.pdf"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    content = input_path.read_text(encoding="utf-8")
    metadata, body = extract_frontmatter(content)

    title = metadata.get("title", input_path.stem.replace("-", " ").title())
    author = resolve_author_name(metadata, default="OpenSciMD")
    translator = metadata.get("translator")
    publisher = metadata.get("publisher", "OpenSciMD")
    year = str(datetime.now().year)
    license_ = metadata.get("license", "Domínio Público")
    date_orig = format_editorial_date(metadata.get("date", ""))
    categories = metadata.get("categories", ["Filosofia"])
    if isinstance(categories, str):
        categories = [categories]
    summary = metadata.get("summary", "")

    # Sanitizar corpo: remover divisores órfãos e seções finais de notas antes do Pandoc
    clean_body = re.sub(r'(?:\r?\n\s*---\s*)+\r?\n+\s*##\s*Nota\s*Editorial\b', '', body)
    clean_body = re.sub(r'##\s*Nota\s*Editorial\s*$', '', clean_body, flags=re.MULTILINE)

    if not shutil.which("pandoc"):
        raise RuntimeError("O executável 'pandoc' não foi encontrado no sistema operacional.")

    # Converter corpo Markdown para Typst usando Pandoc
    cmd = ["pandoc", "-t", "typst", "--shift-heading-level-by=-1"]
    proc = subprocess.run(cmd, input=clean_body, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Erro ao converter Markdown para Typst: {proc.stderr.strip()}")

    body_typst = proc.stdout.strip()

    # Resiliência editorial: eliminar divisores, linhas ou quebras de página órfãs no final do texto
    body_typst = re.sub(r'(\s*#divider\(\)\s*)+$', '', body_typst)
    body_typst = re.sub(r'(\s*#line\([^)]*\)\s*)+$', '', body_typst)
    body_typst = re.sub(r'(\s*#pagebreak\([^)]*\)\s*)+$', '', body_typst)

    template_path = (project_root / "scripts" / "templates" / "book_print.typ").resolve()
    if not template_path.exists():
        raise FileNotFoundError(f"Template Typst não encontrado: {template_path}")

    template_code = template_path.read_text(encoding="utf-8")
    translator_val = f'"{translator}"' if translator else "none"
    cat_items = ", ".join(f'"{c}"' for c in categories) + ("," if len(categories) == 1 else "")

    # Montar documento Typst completo auto-contido
    typst_code = f"""
{template_code}

#show: setup-book.with(
  title: "{title}",
  author: "{author}",
  date-orig: "{date_orig}",
  translator: {translator_val},
  publisher: "{publisher}",
  year: "{year}",
  license: "{license_}",
  categories: ({cat_items}),
  summary: "{summary}",
)

{body_typst}
"""

    tmp_path = out_path.parent / f".tmp_{out_path.stem}.typ"
    tmp_path.write_text(typst_code, encoding="utf-8")

    try:
        typst.compile(str(tmp_path), output=str(out_path), root=str(project_root))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Falha ao gerar miolo impresso em: {out_path}")

    return out_path


def generate_print_cover_spread(
    input_md_path: str | Path,
    interior_pdf_path: str | Path,
    output_cover_pdf_path: Optional[str | Path] = None,
    cover_image_path: Optional[str | Path] = None,
    base_dir: Optional[str | Path] = None,
    paper_type: str = "cream",
) -> Path:
    """Gera a folha gráfica aberta da capa (Quarta capa + Lombada + Frente + Sangria) em PDF."""
    input_path = Path(input_md_path).resolve()
    interior_path = Path(interior_pdf_path).resolve()
    if not interior_path.exists():
        raise FileNotFoundError(f"Miolo em PDF não encontrado para cálculo de capa: {interior_path}")

    project_root = Path(base_dir).resolve() if base_dir else input_path.parent
    while project_root != project_root.parent and not (project_root / "pyproject.toml").exists():
        project_root = project_root.parent

    if output_cover_pdf_path:
        out_cover_path = Path(output_cover_pdf_path).resolve()
    else:
        out_cover_path = interior_path.with_name(f"{input_path.stem}-cover-spread.pdf")

    out_cover_path.parent.mkdir(parents=True, exist_ok=True)

    metadata, _ = extract_frontmatter(input_path.read_text(encoding="utf-8"))
    title = metadata.get("title", input_path.stem.replace("-", " ").title())
    author = resolve_author_name(metadata, default="OpenSciMD")
    summary = metadata.get("summary", "Clássico da literatura e do pensamento filosófico.")
    publisher = metadata.get("publisher", "OpenSciMD")

    # Localizar arte frontal
    resolved_cover = Path(cover_image_path).resolve() if cover_image_path else find_cover_image(input_path, project_root)
    if not resolved_cover or not resolved_cover.exists():
        raise FileNotFoundError(f"Imagem de capa não encontrada para: {input_path}")

    # Calcular dimensões da folha aberta segundo padrões do Amazon KDP
    page_count = get_pdf_page_count(interior_path)
    spine_mm = calculate_kdp_spine_width_mm(page_count, paper_type=paper_type)

    # Padrão KDP 5,5 x 8,5 polegadas (139.7 x 215.9 mm) com qualificação para Distribuição Estendida
    trim_width_mm = 139.7
    trim_height_mm = 215.9
    bleed_mm = 3.2  # 0.125 polegadas de sangria

    total_width_mm = round((trim_width_mm * 2) + spine_mm + (bleed_mm * 2), 2)
    total_height_mm = round(trim_height_mm + (bleed_mm * 2), 2)

    title_upper = title.upper()
    author_upper = author.upper()
    publisher_upper = publisher.upper()

    tmp_cover_path = out_cover_path.parent / f".tmp_{out_cover_path.stem}.typ"
    cover_rel = (
        resolved_cover.relative_to(project_root).as_posix()
        if resolved_cover.is_relative_to(project_root)
        else resolved_cover.as_posix()
    )
    front_cover_path = f"/{cover_rel}" if not cover_rel.startswith("/") else cover_rel

    # Documento Typst da Capa Aberta
    cover_typst = f"""
#set page(
  width: {total_width_mm}mm,
  height: {total_height_mm}mm,
  margin: 0mm,
)

#set text(font: ("Cormorant Garamond", "Liberation Serif", "EB Garamond"), lang: "pt")

#let bleed = {bleed_mm}mm
#let trim-w = {trim_width_mm}mm
#let trim-h = {trim_height_mm}mm
#let spine-w = {spine_mm}mm

#let front-cover = "{front_cover_path}"

// Fundo global da folha com sangria total
#rect(width: 100%, height: 100%, fill: rgb("#111625"), inset: 0mm, outset: 0mm)[
  #grid(
    columns: (trim-w + bleed, spine-w, trim-w + bleed),
    rows: (100%),
    gutter: 0mm,
    
    // --- QUARTA CAPA (VERSO / ESQUERDA) ---
    align(left + horizon)[
      #block(
        width: 82%,
        inset: (left: 24pt, right: 16pt, y: 24pt),
        stroke: none,
      )[
        #set text(fill: rgb("#E2E8F0"))
        #align(left)[
          #text(size: 15pt, weight: "bold", tracking: 0.08em, fill: rgb("#C5A059"))[{title_upper}]\
          #v(0.3em)
          #text(size: 10.5pt, style: "italic", fill: rgb("#A0AEC0"))[{author_upper}]
        ]
        
        #v(1.6em)
        #align(left)[
          #set par(justify: false, spacing: 0.75em)
          #set text(size: 11.5pt)
          #set par(leading: 0.72em)
          {summary}
        ]
      ]
    ],

    // --- LOMBADA (CENTRO) ---
    align(center + horizon)[
      #if spine-w >= 4.0mm [
        #rotate(-90deg)[
          #set text(size: 8.5pt, weight: "bold", fill: rgb("#C5A059"), tracking: 0.12em)
          {title_upper} #h(2.5em) #text(fill: white)[{author_upper}]
        ]
      ]
    ],

    // --- CAPA DA FRENTE COM SANGRIA TOTAL (DIREITA) ---
    align(top + right)[
      #box(width: trim-w + bleed, height: 100%, clip: true)[
        #image(front-cover, width: 100%, height: 100%, fit: "cover")
      ]
    ]
  )
]
"""

    tmp_cover_path.write_text(cover_typst, encoding="utf-8")

    try:
        typst.compile(str(tmp_cover_path), output=str(out_cover_path), root=str(project_root))
    finally:
        if tmp_cover_path.exists():
            tmp_cover_path.unlink()

    if not out_cover_path.exists() or out_cover_path.stat().st_size == 0:
        raise RuntimeError(f"Falha ao gerar capa aberta em: {out_cover_path}")

    return out_cover_path


def convert_md_to_print(
    input_md_path: str | Path,
    base_dir: Optional[str | Path] = None,
    trim_size: str = "14x21",
    paper_type: str = "cream",
) -> Dict[str, Any]:
    """Compila o livro completo para impressão (miolo e capa aberta com lombada)."""
    interior_pdf = convert_md_to_print_interior(
        input_md_path=input_md_path,
        base_dir=base_dir,
        trim_size=trim_size,
    )
    cover_pdf = generate_print_cover_spread(
        input_md_path=input_md_path,
        interior_pdf_path=interior_pdf,
        base_dir=base_dir,
        paper_type=paper_type,
    )
    pages = get_pdf_page_count(interior_pdf)
    spine = calculate_kdp_spine_width_mm(pages, paper_type=paper_type)

    return {
        "source": Path(input_md_path).resolve(),
        "interior_pdf": interior_pdf,
        "cover_pdf": cover_pdf,
        "pages": pages,
        "spine_mm": spine,
        "interior_size_kb": round(interior_pdf.stat().st_size / 1024, 1),
        "cover_size_kb": round(cover_pdf.stat().st_size / 1024, 1),
    }


def batch_convert_print(
    base_dir: Optional[str | Path] = None,
    target_type: str = "books",
) -> Dict[str, Any]:
    """Compila em lote todos os livros para impressão sob demanda."""
    project_root = Path(base_dir).resolve() if base_dir else Path.cwd()
    content_dir = project_root / "content" / "books"
    if not content_dir.exists():
        raise FileNotFoundError(f"Diretório content/books não encontrado: {content_dir}")

    targets = sorted([p for p in content_dir.rglob("*.md") if not p.name.startswith((".", "_"))])
    results: Dict[str, Any] = {
        "total": len(targets),
        "succeeded": [],
        "failed": [],
    }

    for md_path in targets:
        try:
            res = convert_md_to_print(input_md_path=md_path, base_dir=project_root)
            results["succeeded"].append(res)
        except Exception as e:
            results["failed"].append({"source": md_path, "error": str(e)})

    return results
