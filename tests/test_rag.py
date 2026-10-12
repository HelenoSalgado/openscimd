import sqlite3
from pathlib import Path
from scripts.rag import (
    create_schema,
    chunk_markdown,
    sanitize_fts_query,
    build_rag_database,
    search_rag,
    format_ai_prompt_context,
)


def test_create_schema():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    assert "documents" in tables
    assert "chunks" in tables
    assert "chunks_fts" in tables


def test_chunk_markdown_heading_preservation():
    sample = """# Título Principal

Primeiro parágrafo de introdução com texto relevante.

## Seção Filosófica

Texto explicando a dialética socrática.
Mais uma linha de reflexão.

### Subseção

Conclusão da seção.
"""
    chunks = chunk_markdown(sample)
    assert len(chunks) == 3

    headings = [h for h, _ in chunks]
    assert headings == ["Título Principal", "Seção Filosófica", "Subseção"]
    assert "dialética socrática" in chunks[1][1]


def test_sanitize_fts_query():
    assert sanitize_fts_query("sócrates") == "sócrates*"
    assert sanitize_fts_query("amor e caridade") == "amor* AND e* AND caridade*"
    assert sanitize_fts_query("!@#$%") == '""'


def test_build_and_search_rag_temporary(tmp_path):
    base_dir = tmp_path / "repo"
    base_dir.mkdir()

    articles_dir = base_dir / "content" / "articles" / "geral"
    articles_dir.mkdir(parents=True)

    sources_dir = base_dir / "assets" / "sources"
    sources_dir.mkdir(parents=True)

    # Cria fonte pública
    (sources_dir / "artigo-teste.pdf").write_bytes(b"%PDF-1.4 dummy")

    # Cria markdown de artigo
    md_content = """---
id: art_999
title: "O Método Dialético"
author: "Sócrates de Atenas"
categories: ["Filosofia"]
license: "CC-BY-NC-ND-4.0"
date: "2026-01-01"
---

# Introdução

Sócrates dialogava com os cidadãos na ágora de Atenas.

## A Maiêutica

O parto das ideias é a essência do método socrático.
"""
    (articles_dir / "artigo-teste.md").write_text(md_content, encoding="utf-8")

    db_path = tmp_path / "test_rag.sqlite"
    built_path = build_rag_database(base_dir, output_path=db_path)
    assert built_path.exists()

    # Busca com acento
    res_acento = search_rag("sócrates", db_path=db_path, limit=5)
    assert len(res_acento) >= 1
    assert res_acento[0]["doc_title"] == "O Método Dialético"
    assert res_acento[0]["source_path"] == "assets/sources/artigo-teste.pdf"

    # Busca sem acento (insensibilidade FTS5 unicode61)
    res_sem_acento = search_rag("socrates", db_path=db_path, limit=5)
    assert len(res_sem_acento) >= 1
    assert res_sem_acento[0]["doc_title"] == "O Método Dialético"

    # Formatação de prompt para IA
    ai_prompt = format_ai_prompt_context(res_sem_acento)
    assert "Contexto Recuperado do OpenSciMD" in ai_prompt
    assert "Sócrates de Atenas" in ai_prompt
