from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

KindType = Literal["art", "book"]
REGISTRY_RELATIVE_PATH = Path("data") / "catalog-registry.json"
SCHEMA_VERSION = 1


class IdentityViolationError(RuntimeError):
    """Lançada quando uma invariante de imutabilidade de ID é violada."""


@dataclass(frozen=True)
class ScannedDocument:
    """Representa um arquivo Markdown escaneado no repositório sem modificar seu frontmatter."""

    rel_path: str
    title: str
    author: str
    doi: str | None
    body: str
    body_sha256: str
    is_draft: bool
    created_hint_ms: int | None = None


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFD", str(value))
    ascii_text = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    lowered = ascii_text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    raw = str(doi).strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", raw)


def compute_body_sha256(body: str) -> str:
    normalized = body.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_primary_author(metadata: dict[str, Any], fallback: dict[str, Any] | None = None) -> str:
    author = metadata.get("author")
    if author and str(author).strip():
        return str(author).strip()
    authors = metadata.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, dict) and first.get("name"):
            return str(first["name"]).strip()
        if isinstance(first, str) and first.strip():
            return first.strip()
    if fallback:
        if fallback.get("author"):
            return str(fallback["author"]).strip()
        fb_authors = fallback.get("authors")
        if isinstance(fb_authors, list) and fb_authors:
            first = fb_authors[0]
            if isinstance(first, dict) and first.get("name"):
                return str(first["name"]).strip()
            if isinstance(first, str) and first.strip():
                return first.strip()
    return ""


def text_similarity(a: str, b: str) -> float:
    norm_a = normalize_text(a)
    norm_b = normalize_text(b)
    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def body_similarity(body_a: str, body_b: str) -> float:
    sample_a = re.sub(r"\s+", " ", body_a.strip())[:4000]
    sample_b = re.sub(r"\s+", " ", body_b.strip())[:4000]
    if not sample_a and not sample_b:
        return 1.0
    if not sample_a or not sample_b:
        return 0.0
    return SequenceMatcher(None, sample_a, sample_b).ratio()


def parse_id_number(doc_id: str, kind: KindType) -> int:
    prefix = f"{kind}_"
    if not isinstance(doc_id, str) or not doc_id.startswith(prefix):
        return 0
    suffix = doc_id[len(prefix) :]
    return int(suffix) if suffix.isdigit() else 0


def format_doc_id(kind: KindType, num: int) -> str:
    return f"{kind}_{str(num).zfill(3)}"


def detect_git_renames(base_dir: Path, content_subdir: str) -> dict[str, str]:
    """Retorna mapa {novo_rel_path: antigo_rel_path} via histórico recente ou working tree do Git."""
    renames: dict[str, str] = {}
    prefix = f"content/{content_subdir}/"
    git_dir = base_dir / ".git"
    if not git_dir.exists():
        return renames

    commands = [
        ["git", "-C", str(base_dir), "diff", "--find-renames=60%", "--name-status", "HEAD"],
        ["git", "-C", str(base_dir), "log", "-n", "15", "--diff-filter=R", "--find-renames=60%", "--name-status", "--pretty=format:"],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            if proc.returncode != 0 or not proc.stdout:
                continue
            for line in proc.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) >= 3 and parts[0].startswith("R"):
                    old_path = parts[1].strip().replace("\\", "/")
                    new_path = parts[2].strip().replace("\\", "/")
                    if old_path.startswith(prefix) and new_path.startswith(prefix):
                        old_rel = old_path[len(prefix) :]
                        new_rel = new_path[len(prefix) :]
                        if new_rel not in renames:
                            renames[new_rel] = old_rel
        except (OSError, subprocess.SubprocessError):
            continue
    return renames


def _extract_rel_from_remote_url(remote_url: str, content_subdir: str) -> str:
    marker = f"/content/{content_subdir}/"
    if marker in remote_url:
        return remote_url.split(marker)[-1].lstrip("/")
    return remote_url.split("/")[-1]


def validate_registry_snapshot_with_sqlite(
    previous: dict[str, Any] | None,
    candidate: dict[str, Any],
    allow_title_change: bool = False,
) -> None:
    """Valida invariantes relacionais e append-only do ledger usando SQLite em memória."""
    if not isinstance(candidate, dict):
        raise IdentityViolationError("Estrutura do catalog-registry.json inválida.")

    prev_sequences = (previous or {}).get("sequences", {"art": 0, "book": 0})
    cand_sequences = candidate.get("sequences", {})
    for kind in ("art", "book"):
        prev_val = int(prev_sequences.get(kind, 0))
        cand_val = int(cand_sequences.get(kind, 0))
        if cand_val < prev_val:
            raise IdentityViolationError(
                f"High-water mark '{kind}' diminuiu de {prev_val} para {cand_val}."
            )

    prev_entries: dict[str, dict[str, Any]] = (previous or {}).get("entries", {})
    cand_entries: dict[str, dict[str, Any]] = candidate.get("entries", {})

    for prev_id, prev_entry in prev_entries.items():
        if prev_id not in cand_entries:
            raise IdentityViolationError(
                f"Entrada '{prev_id}' ({prev_entry.get('canonical_title')}) foi removida do ledger append-only."
            )

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE TABLE identities (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL CHECK(kind IN ('art', 'book')),
                status TEXT NOT NULL CHECK(status IN ('active', 'draft', 'retired')),
                current_rel_path TEXT NOT NULL,
                doi TEXT,
                canonical_title TEXT NOT NULL,
                canonical_author TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX idx_active_rel_path
            ON identities(kind, current_rel_path)
            WHERE status = 'active'
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX idx_active_doi
            ON identities(kind, LOWER(TRIM(doi)))
            WHERE status = 'active' AND doi IS NOT NULL AND TRIM(doi) != ''
            """
        )

        for entry_id, entry in cand_entries.items():
            kind = entry.get("kind")
            if kind not in ("art", "book"):
                raise IdentityViolationError(f"Kind inválido '{kind}' na entrada '{entry_id}'.")

            id_num = parse_id_number(entry_id, kind)
            if id_num > int(cand_sequences.get(kind, 0)):
                raise IdentityViolationError(
                    f"ID '{entry_id}' excede o high-water mark '{kind}'={cand_sequences.get(kind)}."
                )

            try:
                conn.execute(
                    """
                    INSERT INTO identities (id, kind, status, current_rel_path, doi, canonical_title, canonical_author)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        kind,
                        entry.get("status"),
                        entry.get("current_rel_path") or "",
                        entry.get("doi"),
                        entry.get("canonical_title") or "",
                        entry.get("canonical_author") or "",
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise IdentityViolationError(
                    f"Violação de unicidade relacional para '{entry_id}' ({entry.get('current_rel_path')}): {exc}"
                ) from exc

            prev_entry = prev_entries.get(entry_id)
            if prev_entry:
                if prev_entry.get("kind") != kind:
                    raise IdentityViolationError(
                        f"ID '{entry_id}' alterou tipo de '{prev_entry.get('kind')}' para '{kind}'."
                    )
                if not allow_title_change:
                    same_path = prev_entry.get("current_rel_path") == entry.get("current_rel_path")
                    in_history = entry.get("current_rel_path") in (entry.get("past_rel_paths") or [])
                    same_body = bool(
                        prev_entry.get("last_body_sha256")
                        and prev_entry.get("last_body_sha256") == entry.get("last_body_sha256")
                    )
                    title_sim = text_similarity(
                        str(prev_entry.get("canonical_title") or ""),
                        str(entry.get("canonical_title") or ""),
                    )
                    if not same_path and not in_history and not same_body and title_sim < 0.55:
                        raise IdentityViolationError(
                            f"Suspeita de troca de obra sob o ID '{entry_id}': "
                            f"'{prev_entry.get('canonical_title')}' -> '{entry.get('canonical_title')}'."
                        )
    finally:
        conn.close()


class IdentityRegistry:
    """Gerencia o ledger canônico imutável `data/catalog-registry.json`."""

    def __init__(self, base_dir: Path, data: dict[str, Any], baseline: dict[str, Any] | None = None) -> None:
        self.base_dir = Path(base_dir)
        self.registry_path = self.base_dir / REGISTRY_RELATIVE_PATH
        self.data = data
        self._baseline = baseline if baseline is not None else json.loads(json.dumps(data))

    @classmethod
    def load(cls, base_dir: str | Path, min_high_water: dict[KindType, int] | None = None) -> IdentityRegistry:
        root = Path(base_dir)
        reg_path = root / REGISTRY_RELATIVE_PATH

        if reg_path.exists():
            raw = json.loads(reg_path.read_text(encoding="utf-8"))
            data = {
                "schema_version": int(raw.get("schema_version", SCHEMA_VERSION)),
                "sequences": {
                    "art": int(raw.get("sequences", {}).get("art", 0)),
                    "book": int(raw.get("sequences", {}).get("book", 0)),
                },
                "entries": raw.get("entries", {}),
            }
            baseline = json.loads(json.dumps(data))
            return cls(root, data, baseline)

        # Bootstrap inicial a partir dos index-*.json existentes quando o ledger ainda não foi criado
        entries: dict[str, dict[str, Any]] = {}
        sequences: dict[str, int] = {"art": 0, "book": 0}
        now_ms = int(time.time() * 1000)

        for kind, json_name, list_key, subdir in (
            ("art", "index-articles.json", "articles", "articles"),
            ("book", "index-books.json", "books", "books"),
        ):
            idx_path = root / json_name
            if not idx_path.exists():
                continue
            try:
                idx_data = json.loads(idx_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for item in idx_data.get(list_key, []):
                doc_id = item.get("id")
                if not doc_id or not isinstance(doc_id, str):
                    continue
                num = parse_id_number(doc_id, kind)  # type: ignore[arg-type]
                if num > sequences[kind]:
                    sequences[kind] = num
                rel_path = _extract_rel_from_remote_url(str(item.get("remote_url") or ""), subdir)
                author = extract_primary_author(item)
                ts = int(item.get("published_at") or now_ms)
                entries[doc_id] = {
                    "id": doc_id,
                    "kind": kind,
                    "status": "active",
                    "current_rel_path": rel_path,
                    "past_rel_paths": [],
                    "canonical_title": str(item.get("title") or rel_path),
                    "canonical_author": author,
                    "doi": normalize_doi(item.get("doi")) or None,
                    "first_body_sha256": None,
                    "last_body_sha256": None,
                    "created_at": ts,
                    "updated_at": ts,
                    "retired_at": None,
                }

        if min_high_water:
            for k, val in min_high_water.items():
                if int(val) > sequences[k]:
                    sequences[k] = int(val)

        data = {
            "schema_version": SCHEMA_VERSION,
            "sequences": sequences,
            "entries": entries,
        }
        return cls(root, data, baseline=None)

    def _find_candidates(self, kind: KindType) -> list[dict[str, Any]]:
        return [e for e in self.data["entries"].values() if e.get("kind") == kind]

    def reconcile_kind(
        self,
        kind: KindType,
        scanned_docs: list[ScannedDocument],
        content_subdir: str,
        now_ms: int | None = None,
    ) -> dict[str, str]:
        """Resolve e trava IDs imutáveis para todos os documentos escaneados de um tipo."""
        timestamp_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        entries: dict[str, dict[str, Any]] = self.data["entries"]
        git_renames = detect_git_renames(self.base_dir, content_subdir)
        scanned_paths = {doc.rel_path for doc in scanned_docs}

        matched_ids: set[str] = set()
        resolved_by_rel: dict[str, str] = {}

        def bind_doc_to_entry(doc: ScannedDocument, entry: dict[str, Any]) -> None:
            doc_id = str(entry["id"])
            matched_ids.add(doc_id)
            resolved_by_rel[doc.rel_path] = doc_id

            target_status = "draft" if doc.is_draft else "active"
            old_path = str(entry.get("current_rel_path") or "")
            past_paths: list[str] = list(entry.get("past_rel_paths") or [])
            path_changed = old_path != doc.rel_path

            if path_changed and old_path and old_path not in past_paths:
                past_paths.append(old_path)
            # Remove novo caminho de aliases se estava lá anteriormente
            if doc.rel_path in past_paths:
                past_paths = [p for p in past_paths if p != doc.rel_path]

            norm_doi = normalize_doi(doc.doi) or None
            first_sha = entry.get("first_body_sha256") or doc.body_sha256

            changed = (
                entry.get("status") != target_status
                or path_changed
                or past_paths != (entry.get("past_rel_paths") or [])
                or entry.get("canonical_title") != doc.title
                or (doc.author and entry.get("canonical_author") != doc.author)
                or (norm_doi and entry.get("doi") != norm_doi)
                or entry.get("first_body_sha256") != first_sha
                or entry.get("last_body_sha256") != doc.body_sha256
            )

            entry["status"] = target_status
            entry["current_rel_path"] = doc.rel_path
            entry["past_rel_paths"] = past_paths
            entry["canonical_title"] = doc.title
            if doc.author:
                entry["canonical_author"] = doc.author
            if norm_doi:
                entry["doi"] = norm_doi
            entry["first_body_sha256"] = first_sha
            entry["last_body_sha256"] = doc.body_sha256
            if target_status != "retired":
                entry["retired_at"] = None
            if changed:
                entry["updated_at"] = timestamp_ms

        def find_unmatched_entries() -> list[dict[str, Any]]:
            return [e for e in self._find_candidates(kind) if str(e["id"]) not in matched_ids]

        # Passagem 1: Match exato por current_rel_path ou past_rel_paths ou git rename
        unmatched_docs: list[ScannedDocument] = []
        for doc in scanned_docs:
            candidates = find_unmatched_entries()
            by_current = next((e for e in candidates if e.get("current_rel_path") == doc.rel_path), None)
            if by_current is not None:
                bind_doc_to_entry(doc, by_current)
                continue

            by_alias = next((e for e in candidates if doc.rel_path in (e.get("past_rel_paths") or [])), None)
            if by_alias is not None:
                bind_doc_to_entry(doc, by_alias)
                continue

            git_old_rel = git_renames.get(doc.rel_path)
            if git_old_rel and git_old_rel not in scanned_paths:
                by_git = next(
                    (
                        e
                        for e in candidates
                        if e.get("current_rel_path") == git_old_rel or git_old_rel in (e.get("past_rel_paths") or [])
                    ),
                    None,
                )
                if by_git is not None:
                    bind_doc_to_entry(doc, by_git)
                    continue

            unmatched_docs.append(doc)

        # Passagem 2: Match por DOI ou hash do corpo (quando o caminho antigo não está ocupado)
        still_unmatched: list[ScannedDocument] = []
        for doc in unmatched_docs:
            candidates = [
                e for e in find_unmatched_entries() if e.get("current_rel_path") not in scanned_paths
            ]
            doc_doi = normalize_doi(doc.doi)
            if doc_doi:
                by_doi = next((e for e in candidates if normalize_doi(e.get("doi")) == doc_doi), None)
                if by_doi is not None:
                    bind_doc_to_entry(doc, by_doi)
                    continue

            by_hash = next(
                (
                    e
                    for e in candidates
                    if (e.get("last_body_sha256") and e.get("last_body_sha256") == doc.body_sha256)
                    or (e.get("first_body_sha256") and e.get("first_body_sha256") == doc.body_sha256)
                ),
                None,
            )
            if by_hash is not None:
                bind_doc_to_entry(doc, by_hash)
                continue

            still_unmatched.append(doc)

        # Passagem 3: Guarda semântica para arquivos movidos e editados simultaneamente
        for doc in still_unmatched:
            orphan_candidates = [
                e for e in find_unmatched_entries() if e.get("current_rel_path") not in scanned_paths
            ]
            semantic_match: dict[str, Any] | None = None
            for cand in orphan_candidates:
                t_sim = text_similarity(str(cand.get("canonical_title") or ""), doc.title)
                cand_author = str(cand.get("canonical_author") or "")
                a_sim = 1.0 if (not cand_author or not doc.author) else text_similarity(cand_author, doc.author)
                if t_sim >= 0.85 and a_sim >= 0.75:
                    semantic_match = cand
                    break

            if semantic_match is not None:
                bind_doc_to_entry(doc, semantic_match)
                continue

            # Obra verdadeiramente inédita: aloca próximo número monotônico
            seq = int(self.data["sequences"].get(kind, 0))
            while True:
                seq += 1
                new_id = format_doc_id(kind, seq)
                if new_id not in entries:
                    break
            self.data["sequences"][kind] = seq

            created_ts = int(doc.created_hint_ms or timestamp_ms)
            entries[new_id] = {
                "id": new_id,
                "kind": kind,
                "status": "draft" if doc.is_draft else "active",
                "current_rel_path": doc.rel_path,
                "past_rel_paths": [],
                "canonical_title": doc.title,
                "canonical_author": doc.author,
                "doi": normalize_doi(doc.doi) or None,
                "first_body_sha256": doc.body_sha256,
                "last_body_sha256": doc.body_sha256,
                "created_at": created_ts,
                "updated_at": timestamp_ms,
                "retired_at": None,
            }
            matched_ids.add(new_id)
            resolved_by_rel[doc.rel_path] = new_id

        # Passagem 4: Aposentadoria segura (Tombstone) para entradas não encontradas no disco
        for entry in self._find_candidates(kind):
            doc_id = str(entry["id"])
            if doc_id not in matched_ids and entry.get("status") != "retired":
                entry["status"] = "retired"
                entry["retired_at"] = entry.get("retired_at") or timestamp_ms
                entry["updated_at"] = timestamp_ms

        return resolved_by_rel

    def save(self) -> bool:
        """Valida invariantes via SQLite em memória e grava o JSON determinístico se houve mudança."""
        # Ordena chaves deterministicamente para manter diffs do Git sempre limpos
        sorted_entries = {
            k: self.data["entries"][k]
            for k in sorted(self.data["entries"].keys())
        }
        candidate = {
            "schema_version": SCHEMA_VERSION,
            "sequences": {
                "art": int(self.data["sequences"].get("art", 0)),
                "book": int(self.data["sequences"].get("book", 0)),
            },
            "entries": sorted_entries,
        }

        validate_registry_snapshot_with_sqlite(self._baseline, candidate)

        if self._baseline == candidate and self.registry_path.exists():
            return False

        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(candidate, f, indent=2, ensure_ascii=False)
            f.write("\n")

        self.data = candidate
        self._baseline = json.loads(json.dumps(candidate))
        return True
