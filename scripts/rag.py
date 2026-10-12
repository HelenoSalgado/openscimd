"""Módulo de indexação e recuperação RAG (Retrieval-Augmented Generation) do OpenSciMD.

Fornece compilação de banco de dados SQLite local com FTS5 (Full-Text Search)
para pesquisa semântico-textual de alta precisão e injeção de contexto em chats de IA.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.utils import parse_markdown_file, get_files_recursively


def create_schema(conn: sqlite3.Connection) -> None:
    """Cria o esquema relacional e as tabelas virtuais FTS5."""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        date TEXT,
        categories TEXT,
        udc TEXT,
        doi TEXT,
        license TEXT,
        summary TEXT,
        markdown_path TEXT NOT NULL,
        source_path TEXT,
        remote_url TEXT,
        reading_time_min INTEGER,
        word_count INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_slug TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        heading TEXT,
        content TEXT NOT NULL,
        char_count INTEGER NOT NULL,
        FOREIGN KEY (doc_slug) REFERENCES documents (slug) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_chunks_doc_slug ON chunks (doc_slug);
    """)

    # Tabela virtual FTS5 para busca textual com suporte unicode e remoção de acentos
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        doc_slug UNINDEXED,
        heading,
        content,
        tokenize='unicode61 remove_diacritics 2'
    );
    """)

    conn.commit()


def chunk_markdown(content: str, max_chunk_chars: int = 1500) -> List[Tuple[str, str]]:
    """Segmenta o Markdown preservando cabeçalhos e parágrafos coerentes.

    Retorna uma lista de tuplas: (heading_context, chunk_text).
    """
    lines = content.splitlines()
    chunks: List[Tuple[str, str]] = []

    current_heading = "Introdução"
    current_block: List[str] = []
    current_chars = 0

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            # Novo cabeçalho: finaliza o bloco anterior se houver
            if current_block:
                block_text = "\n".join(current_block).strip()
                if block_text:
                    chunks.append((current_heading, block_text))
                current_block = []
                current_chars = 0
            current_heading = match.group(2).strip()
            continue

        # Linha em branco ou parágrafo
        if not line.strip() and current_chars >= max_chunk_chars:
            block_text = "\n".join(current_block).strip()
            if block_text:
                chunks.append((current_heading, block_text))
            current_block = []
            current_chars = 0
            continue

        current_block.append(line)
        current_chars += len(line) + 1

    if current_block:
        block_text = "\n".join(current_block).strip()
        if block_text:
            chunks.append((current_heading, block_text))

    return chunks


def resolve_source_file(base_dir: Path, slug: str) -> Optional[str]:
    """Localiza o arquivo-fonte correspondente em assets/sources/."""
    sources_dir = base_dir / "assets" / "sources"
    if not sources_dir.exists():
        return None

    matches = list(sources_dir.glob(f"{slug}.*"))
    if matches:
        return matches[0].relative_to(base_dir).as_posix()
    return None


def build_rag_database(
    base_dir: str | Path,
    output_path: Optional[str | Path] = None,
) -> Path:
    """Compila o banco de dados SQLite RAG a partir de content/ e índices."""
    base_path = Path(base_dir).resolve()
    db_path = Path(output_path).resolve() if output_path else base_path / "data" / "openscimd_rag.sqlite"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        create_schema(conn)
        cursor = conn.cursor()

        collections = [
            ("article", base_path / "content" / "articles"),
            ("book", base_path / "content" / "books"),
        ]

        total_docs = 0
        total_chunks = 0

        for doc_type, folder in collections:
            if not folder.exists():
                continue

            md_files = [Path(p) for p in get_files_recursively(folder)]

            for md_file in md_files:
                slug = md_file.stem
                rel_path = md_file.relative_to(base_path).as_posix()
                parsed = parse_markdown_file(md_file)
                meta = parsed.get("metadata", {})
                body = parsed.get("body", "")

                doc_id = meta.get("id") or f"{doc_type[:3]}_{slug}"
                title = meta.get("title") or slug.replace("-", " ").title()
                authors = meta.get("authors") or meta.get("author") or "Desconhecido"
                if isinstance(authors, list):
                    author_str = ", ".join(
                        a.get("name", str(a)) if isinstance(a, dict) else str(a)
                        for a in authors
                    )
                else:
                    author_str = str(authors)

                categories = meta.get("categories") or meta.get("category") or []
                categories_json = json.dumps(categories, ensure_ascii=False)
                summary = meta.get("summary") or ""
                date_str = str(meta.get("date") or "")
                udc_val = str(meta.get("udc") or meta.get("UDC") or "")
                doi_val = str(meta.get("doi") or meta.get("DOI") or "")
                license_val = str(meta.get("license") or meta.get("licence") or "CC-BY-NC-ND-4.0")

                words = len(body.split())
                reading_time = max(1, words // 200)
                source_file = resolve_source_file(base_path, slug)
                remote_url = f"https://github.com/HelenoSalgado/openscimd/blob/main/{rel_path}"

                cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    id, slug, type, title, author, date, categories,
                    udc, doi, license, summary, markdown_path,
                    source_path, remote_url, reading_time_min, word_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    doc_id, slug, doc_type, title, author_str, date_str, categories_json,
                    udc_val, doi_val, license_val, summary, rel_path,
                    source_file, remote_url, reading_time, words
                ))
                total_docs += 1

                # Gerar e gravar chunks
                raw_chunks = chunk_markdown(body)
                for idx, (heading, chunk_text) in enumerate(raw_chunks, start=1):
                    cursor.execute("""
                    INSERT INTO chunks (doc_slug, chunk_index, heading, content, char_count)
                    VALUES (?, ?, ?, ?, ?);
                    """, (slug, idx, heading, chunk_text, len(chunk_text)))

                    cursor.execute("""
                    INSERT INTO chunks_fts (doc_slug, heading, content)
                    VALUES (?, ?, ?);
                    """, (slug, heading, chunk_text))
                    total_chunks += 1

        conn.commit()
    finally:
        conn.close()

    return db_path


def sanitize_fts_query(query: str) -> str:
    """Prepara a query para o motor FTS5 tratando operadores e caracteres especiais."""
    cleaned = re.sub(r'[^\w\s]', ' ', query, flags=re.UNICODE)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    if not tokens:
        return '""'
    return " AND ".join(f"{tok}*" for tok in tokens)


def search_rag(
    query: str,
    db_path: str | Path = "data/openscimd_rag.sqlite",
    limit: int = 5,
    doc_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Executa busca semântico-textual BM25 via FTS5 e retorna trechos rankeados."""
    target_db = Path(db_path)
    if not target_db.exists():
        raise FileNotFoundError(f"Banco de dados RAG não localizado em: {target_db}. Execute 'openscimd build-rag' primeiro.")

    fts_query = sanitize_fts_query(query)

    conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    results: List[Dict[str, Any]] = []

    try:
        cursor = conn.cursor()
        type_filter = "AND d.type = ?" if doc_type else ""
        params: List[Any] = [fts_query]
        if doc_type:
            params.append(doc_type)
        params.append(limit)

        sql = f"""
        SELECT 
            c.id AS chunk_id,
            c.doc_slug,
            c.heading,
            c.content,
            d.title AS doc_title,
            d.author AS doc_author,
            d.type AS doc_type,
            d.markdown_path,
            d.source_path,
            d.license AS doc_license,
            bm25(chunks_fts) AS rank,
            snippet(chunks_fts, 2, '【', '】', '...', 25) AS highlighted_snippet
        FROM chunks_fts
        JOIN chunks c ON c.rowid = chunks_fts.rowid
        JOIN documents d ON d.slug = c.doc_slug
        WHERE chunks_fts MATCH ?
        {type_filter}
        ORDER BY rank
        LIMIT ?;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        for row in rows:
            results.append({
                "chunk_id": row["chunk_id"],
                "doc_slug": row["doc_slug"],
                "doc_title": row["doc_title"],
                "doc_author": row["doc_author"],
                "doc_type": row["doc_type"],
                "heading": row["heading"],
                "content": row["content"],
                "highlighted_snippet": row["highlighted_snippet"],
                "markdown_path": row["markdown_path"],
                "source_path": row["source_path"],
                "license": row["doc_license"],
                "rank_score": round(float(row["rank"]), 4),
            })
    finally:
        conn.close()

    return results


def format_ai_prompt_context(results: List[Dict[str, Any]]) -> str:
    """Formata os resultados da busca em um bloco de contexto pronto para injeção em chat de IA."""
    if not results:
        return "Nenhum documento relevante encontrado na base OpenSciMD."

    output_lines = [
        "### Contexto Recuperado do OpenSciMD:",
        "",
    ]

    for idx, r in enumerate(results, start=1):
        source_info = f" (Fonte Primária: `{r['source_path']}`)" if r["source_path"] else ""
        output_lines.extend([
            f"#### [{idx}] {r['doc_title']} — {r['doc_author']} ({r['doc_type'].upper()})",
            f"* **Seção:** {r['heading']}",
            f"* **Arquivo Local:** `{r['markdown_path']}`{source_info}",
            f"* **Licença:** {r['license']}",
            "",
            "```markdown",
            r["content"],
            "```",
            "",
        ])

    return "\n".join(output_lines)
