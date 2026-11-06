#!/usr/bin/env python3
"""Conversor Editorial de Markdown para EPUB 3 com metadados semânticos e folha de estilo clássica."""

import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extrai metadados do YAML frontmatter e separa o corpo do Markdown."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        raw_yaml, body = match.groups()
        try:
            metadata = yaml.safe_load(raw_yaml) or {}
            return metadata, body
        except yaml.YAMLError:
            return {}, content
    return {}, content


def find_cover_image(book_path: Path, base_dir: Optional[Path] = None) -> Optional[Path]:
    """Localiza a arte de capa correspondente ao livro nos diretórios de assets."""
    if base_dir is None:
        base_dir = book_path.resolve().parents[2] if len(book_path.resolve().parents) >= 3 else Path.cwd()

    stem = book_path.stem
    candidates = [
        base_dir / "assets" / "covers" / "originals" / f"{stem}.png",
        base_dir / "assets" / "covers" / "originals" / f"{stem}.jpg",
        base_dir / "assets" / "covers" / "originals" / f"{stem}.jpeg",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.png",
        base_dir / "assets" / "covers" / "desktop" / f"{stem}.jpg",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def get_default_css_path(base_dir: Optional[Path] = None) -> Optional[Path]:
    """Retorna o caminho da folha de estilo editorial padrão para EPUB."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    css_candidate = base_dir / "scripts" / "templates" / "epub.css"
    if css_candidate.exists():
        return css_candidate
    return None


def generate_frontmatter_editorial_blocks(metadata: Dict[str, Any], prefix: str = "##") -> str:
    """Gera blocos pré-textuais editoriais: Folha de Rosto e Ficha Catalográfica."""
    title = metadata.get("title", "Obra")
    author = metadata.get("author", "Autor Desconhecido")
    translator = metadata.get("translator")
    publisher = metadata.get("publisher", "OpenSciMD")
    year = datetime.now().year
    license_ = metadata.get("license", "Domínio Público")
    date_orig = metadata.get("date", "")
    categories = metadata.get("categories", ["Filosofia"])
    cat_str = ", ".join(categories) if isinstance(categories, list) else str(categories)

    blocks = [
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="editorial-titlepage">',
        f'<div class="main-title">{title}</div>',
    ]

    if date_orig:
        blocks.append(f'<div class="sub-title">Composição canônica: {date_orig}</div>')

    blocks.append(f'<div class="author-name">{author}</div>')

    if translator:
        blocks.append(f'<div class="translator-info">Traduzido por {translator}</div>')

    blocks.extend([
        '</div>\n',
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="catalographic-wrapper">',
        '<div class="catalographic-box">',
        '<h4>Dados Internacionais de Catalogação na Publicação (CIP)</h4>',
        f'<p><strong>{author}</strong></p>',
        f'<p><em>{title}</em> / {author}' + (f' ; tradução de {translator}' if translator else '') + f'. — {publisher}, {year}.</p>',
    ])

    if date_orig:
        blocks.append(f'<p>Datação original da obra: {date_orig}.</p>')

    blocks.extend([
        f'<p>Assunto(s): {cat_str}.</p>',
        f'<p>Licença Editorial: {license_}.</p>',
        '<p>Publicação digital aberta de livre difusão cultural e científica.</p>',
        '</div>\n',
        '</div>\n',
    ])

    return "\n".join(blocks)


def generate_colophon_markdown(metadata: Dict[str, Any], prefix: str = "##") -> str:
    """Gera bloco editorial final (colofão) com dados do selo OpenSciMD e tradução."""
    title = metadata.get("title", "Obra")
    author = metadata.get("author", "Autor Desconhecido")
    translator = metadata.get("translator")
    publisher = metadata.get("publisher", "OpenSciMD")
    license_ = metadata.get("license", "Domínio Público")
    year = datetime.now().year

    colophon = [
        '\n\n<div class="colophon-box">',
        f"<h4>{publisher} · Edições Abertas</h4>",
        f"<p><strong>{title}</strong> — {author}</p>",
    ]

    if translator:
        colophon.append(f"<p>Traduzido por {translator}</p>")

    colophon.extend([
        f"<p><em>Licença Editorial:</em> {license_}</p>",
        "<p>Projeto OpenSciMD: Difusão científica, literária e filosófica em formatos abertos.</p>",
        "<p>Composto digitalmente em tipos clássicos Garamond.</p>",
        f"<small>© {year} {publisher} · Livro Digital EPUB 3</small>",
        "</div>\n"
    ])

    return "\n".join(colophon)


def generate_institutional_page(prefix: str = "##") -> str:
    """Gera página institucional final apresentando OpenSciMD, Leia-me e citação acadêmica."""
    blocks = [
        f"{prefix} {{.unnumbered .unlisted}}\n",
        '<div class="institutional-wrapper">',
        '<div class="institutional-card">',
        '<div class="institutional-badge">OpenSciMD &amp; Leia-me</div>',
        '<h3>Conhecimento Aberto, Leitura Ativa</h3>',
        '<p class="institutional-lead">',
        'Esta edição digital foi produzida pelo <strong>OpenSciMD</strong>, uma iniciativa voltada à curadoria, normalização semântica e preservação de tratados clássicos e artigos acadêmicos em formatos digitais abertos e acessíveis.',
        '</p>',
        '<div class="institutional-section">',
        '<h4>Aplicativo Oficial Leia-me</h4>',
        '<p>',
        'Para uma experiência aprofundada de estudo e pesquisa, utilize o aplicativo <strong>Leia-me</strong>. Desenvolvido para o público estudantil e acadêmico, o app oferece:',
        '</p>',
        '<ul>',
        '<li>Leitura imersiva em Markdown e navegação por sumário interativo;</li>',
        '<li>Busca aprofundada (FTS) com suporte a termos gregos, latinos e notas;</li>',
        '<li>Caderno de anotações e realces coloridos vinculados aos trechos;</li>',
        '<li>Acesso completo e leitura 100% offline no seu dispositivo.</li>',
        '<li>Dicionário da Língua Portuguêsa integrado.</li>',
        '</ul>',
        '<p class="institutional-link-box">',
        'Conheça: <a href="https://leiame.app">leiame.app</a>',
        '</p>',
        '</div>',
        '<div class="institutional-section">',
        '<h4>Licença Editorial e Como Citar</h4>',
        '<p>',
        'A compilação editorial, normalização tipográfica e identidade gráfica desta edição estão protegidas sob a licença <strong>Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)</strong>.',
        '</p>',
        '<p>',
        'Você é livre para baixar, armazenar e compartilhar esta edição sem finalidade comercial e preservando a integridade original. Para fins de pesquisa, referência acadêmica ou redistribuição, cite a compilação:',
        '</p>',
        '<p class="citation-box">',
        '<code>Salgado, H. (2026). OpenSciMD: Open-Access Scientific Articles in Markdown (Version 1.1.0) [Data set]. https://github.com/HelenoSalgado/openscimd</code>',
        '</p>',
        '<p class="institutional-repo">',
        'Repositório: <a href="https://github.com/HelenoSalgado/openscimd">github.com/HelenoSalgado/openscimd</a>',
        '</p>',
        '</div>',
        '</div>\n',
        '</div>\n',
    ]
    return "\n".join(blocks)


def _clean_epub_container(epub_path: Path) -> None:
    """Higieniza os documentos XHTML do EPUB removendo cabeçalhos unnumbered sintetizados pelo Pandoc."""
    import zipfile
    temp_epub = epub_path.with_suffix(".tmp.epub")
    with zipfile.ZipFile(epub_path, "r") as z_in, zipfile.ZipFile(temp_epub, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
        for item in z_in.infolist():
            data = z_in.read(item.filename)
            if item.filename.endswith(".xhtml"):
                text = data.decode("utf-8")
                if "editorial-titlepage" in text or "catalographic-box" in text or "institutional-card" in text:
                    text = re.sub(r'<h1 class="unnumbered[^"]*">.*?</h1>\s*', '', text, flags=re.DOTALL)
                    data = text.encode("utf-8")
            if item.filename == "mimetype":
                z_out.writestr(item, data, compress_type=zipfile.ZIP_STORED)
            else:
                z_out.writestr(item, data)
    temp_epub.replace(epub_path)


def convert_md_to_epub(
    input_md_path: str | Path,
    output_epub_path: Optional[str | Path] = None,
    cover_path: Optional[str | Path] = None,
    css_path: Optional[str | Path] = None,
    base_dir: Optional[str | Path] = None,
    add_colophon: bool = False,
    add_editorial_pages: bool = True,
    add_institutional_page: bool = True,
) -> Path:
    """Converte um documento Markdown para formato EPUB 3 profissional com Pandoc."""
    input_path = Path(input_md_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {input_path}")

    project_root = Path(base_dir).resolve() if base_dir else input_path.parent
    while project_root != project_root.parent and not (project_root / "pyproject.toml").exists():
        project_root = project_root.parent

    if output_epub_path:
        out_path = Path(output_epub_path).resolve()
    else:
        dist_dir = project_root / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        out_path = dist_dir / f"{input_path.stem}.epub"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Verificar pandoc no ambiente
    if not shutil.which("pandoc"):
        raise RuntimeError("O executável 'pandoc' não foi encontrado no sistema operacional.")

    content = input_path.read_text(encoding="utf-8")
    metadata, body = extract_frontmatter(content)

    # Resolver metadados essenciais
    title = metadata.get("title", input_path.stem.replace("-", " ").title())
    author = metadata.get("author", "OpenSciMD")
    translator = metadata.get("translator")
    lang = metadata.get("language", "pt-BR")
    summary = metadata.get("summary", "")
    rights = metadata.get("license", "Domínio Público")

    # Localizar capa se não fornecida
    resolved_cover: Optional[Path] = None
    if cover_path:
        resolved_cover = Path(cover_path).resolve()
        if not resolved_cover.exists():
            raise FileNotFoundError(f"Arquivo de capa não encontrado: {cover_path}")
    else:
        resolved_cover = find_cover_image(input_path, project_root)

    # Localizar folha de estilo
    resolved_css: Optional[Path] = None
    if css_path:
        resolved_css = Path(css_path).resolve()
    else:
        resolved_css = get_default_css_path(project_root)

    # Analisar o nível do primeiro cabeçalho no corpo para normalização perfeita de capítulos
    first_heading_match = re.search(r"^(#{1,6})\s+", body, re.MULTILINE)
    top_heading_level = len(first_heading_match.group(1)) if first_heading_match else 1
    shift_heading = (top_heading_level == 2)
    heading_prefix = "##" if shift_heading else "#"

    # Construir corpo editorial ordenado
    markdown_parts = []

    # 1. Elementos pré-textuais (Folha de Rosto e Ficha Catalográfica)
    if add_editorial_pages:
        editorial_pre = generate_frontmatter_editorial_blocks(metadata, prefix=heading_prefix)
        markdown_parts.append(editorial_pre)

    # 2. Corpo do texto (com higienização de âncoras vazias de notas)
    clean_body = re.sub(r'---\s*\n+##\s+Nota Editorial\s*\n+(?=\[\^)', '', body)
    markdown_parts.append(clean_body.strip())

    # 3. Elementos pós-textuais (Colofão e Página Institucional)
    if add_colophon:
        colophon_md = generate_colophon_markdown(metadata, prefix=heading_prefix)
        markdown_parts.append(colophon_md)

    if add_institutional_page:
        institutional_md = generate_institutional_page(prefix=heading_prefix)
        markdown_parts.append(institutional_md)

    compiled_markdown = "\n\n".join(markdown_parts)

    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp_file:
        tmp_file.write(compiled_markdown)
        tmp_file_path = Path(tmp_file.name)

    try:
        cmd = [
            "pandoc",
            str(tmp_file_path),
            "-o",
            str(out_path),
            "-t",
            "epub3",
            "--epub-title-page=false",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            f"--metadata=title:{title}",
            f"--metadata=author:{author}",
            f"--metadata=lang:{lang}",
            "--metadata=publisher:OpenSciMD",
        ]

        if shift_heading:
            cmd.append("--shift-heading-level-by=-1")

        if translator:
            cmd.append(f"--metadata=contributor:{translator} (Tradutor)")

        if summary:
            cmd.append(f"--metadata=description:{summary}")

        if rights:
            cmd.append(f"--metadata=rights:{rights}")

        if resolved_css and resolved_css.exists():
            cmd.append(f"--css={resolved_css}")

        if resolved_cover and resolved_cover.exists():
            cmd.append(f"--epub-cover-image={resolved_cover}")

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Erro ao executar pandoc: {proc.stderr.strip()}")

    finally:
        if tmp_file_path.exists():
            tmp_file_path.unlink()

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Falha ao gerar arquivo EPUB em {out_path}")

    # Higienizar EPUB para suprimir títulos sintetizados repetidos
    _clean_epub_container(out_path)

    return out_path
