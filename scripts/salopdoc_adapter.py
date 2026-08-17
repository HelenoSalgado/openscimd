"""Adaptador do SalopDoc para o ecossistema OpenSciMD.

Fornece funções de alto nível para conversão de PDFs, processamento em lote
e normalização semântica de arquivos Markdown legados.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import salopdoc
from salopdoc.config import ConfigLoader, SalopDocConfig


def get_default_config(base_dir: str | Path | None = None) -> SalopDocConfig:
    """Carrega a configuração do salopdoc.yml a partir do diretório base."""
    root = Path(base_dir) if base_dir else Path.cwd()
    config_file = root / "salopdoc.yml"
    
    if config_file.exists():
        return ConfigLoader.load(config_file)
    return ConfigLoader.load()


def import_pdf(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    base_dir: str | Path | None = None,
    title: str | None = None,
    author: str | None = None,
    date: str | None = None,
) -> Path:
    """Converte um único documento PDF em Markdown rico com Frontmatter e reflow semântico.
    
    Args:
        pdf_path: Caminho para o arquivo PDF original.
        output_path: Caminho de saída opcional para o arquivo Markdown.
        base_dir: Diretório raiz do projeto.
        title: Sobrescreve o título detectado se fornecido.
        author: Sobrescreve a autoria se fornecida.
        date: Sobrescreve a data se fornecida.
        
    Returns:
        Path do arquivo Markdown gerado.
    """
    pdf_file = Path(pdf_path).resolve()
    if not pdf_file.exists():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_file}")

    config = get_default_config(base_dir)
    converter = salopdoc.SalopDocConverter(config)
    
    out_file = Path(output_path).resolve() if output_path else None
    result_path = converter.convert_pdf_file(
        pdf_path=pdf_file,
        output_path=out_file,
        title=title,
        author=author,
        date=date,
    )
    return Path(result_path)


def batch_import(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    base_dir: str | Path | None = None,
) -> List[Path]:
    """Processa todos os PDFs de uma pasta de entrada em lote.
    
    Args:
        input_dir: Diretório contendo PDFs brutos (default: data/raw).
        output_dir: Diretório de destino dos rascunhos (default: data/draft).
        base_dir: Diretório raiz do projeto.
        
    Returns:
        Lista de caminhos dos arquivos Markdown gerados.
    """
    config = get_default_config(base_dir)
    
    in_dir = Path(input_dir) if input_dir else Path(config.paths.input_dir)
    out_dir = Path(output_dir) if output_dir else Path(config.paths.output_dir)
    
    if not in_dir.is_absolute() and base_dir:
        in_dir = Path(base_dir) / in_dir
    if not out_dir.is_absolute() and base_dir:
        out_dir = Path(base_dir) / out_dir
        
    in_dir = in_dir.resolve()
    out_dir = out_dir.resolve()
    
    if not in_dir.exists():
        raise FileNotFoundError(f"Diretório de entrada não encontrado: {in_dir}")
        
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(list(in_dir.glob("*.pdf")) + list(in_dir.glob("*.PDF")))
    
    if not pdf_files:
        print(f"⚠️ Nenhum arquivo PDF encontrado em: {in_dir}")
        return []
        
    print(f"📦 Encontrados {len(pdf_files)} PDFs em {in_dir}. Iniciando processamento em lote...")
    
    converter = salopdoc.SalopDocConverter(config)
    generated_files: List[Path] = []
    
    for idx, pdf in enumerate(pdf_files, 1):
        target_md = out_dir / f"{pdf.stem}.md"
        print(f"  [{idx}/{len(pdf_files)}] Convertendo: {pdf.name} -> {target_md.name}")
        try:
            res = converter.convert_pdf_file(pdf_path=pdf, output_path=target_md)
            generated_files.append(Path(res))
            print(f"  ✅ Concluído: {target_md.name}")
        except Exception as e:
            print(f"  ❌ Erro ao converter {pdf.name}: {e}")
            
    print(f"\n🎉 Lote finalizado! {len(generated_files)}/{len(pdf_files)} arquivos processados com sucesso.")
    return generated_files


def clean_markdown_file(
    file_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Normaliza um arquivo Markdown legado aplicando regras tipográficas e estruturais.
    
    Args:
        file_path: Caminho do arquivo Markdown a ser limpo.
        output_path: Caminho de saída opcional. Se não for especificado, sobrescreve o original.
        
    Returns:
        Path do arquivo Markdown limpo.
    """
    src_file = Path(file_path).resolve()
    if not src_file.exists():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {src_file}")
        
    target_file = Path(output_path).resolve() if output_path else src_file
    
    with open(src_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Aplicar pipeline de normalizações semânticas e tipográficas do salopdoc
    quote_converter = salopdoc.QuoteConverter()
    text_normalizer = salopdoc.TextNormalizer()
    heading_organizer = salopdoc.HeadingOrganizer()
    
    clean_text = quote_converter.convert(content)
    clean_text = text_normalizer.normalize(clean_text)
    clean_text = heading_organizer.process(clean_text)
    
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(clean_text)
        
    return target_file
