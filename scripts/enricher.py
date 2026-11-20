"""Enriquecedor de metadados YAML via APIs oficiais do Crossref e Zenodo."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import requests
import yaml

_ZENODO_DOI_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/)?10\.5281/zenodo\.(\d+)$", re.IGNORECASE)
_COMPOSITE_ISSUE_RE = re.compile(r"^(\d+)\((\d+)\)$")


def _normalize_doi(doi: str) -> str:
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(doi).strip(), flags=re.IGNORECASE)


def _normalize_pages(pages_val: Any) -> str:
    raw = str(pages_val).strip()
    if re.fullmatch(r"\d+-\d+", raw):
        return raw.replace("-", "–")
    return raw


def _coerce_int_or_str(val: Any) -> int | str:
    raw = str(val).strip()
    return int(raw) if raw.isdigit() else raw


def _resolve_issue_and_volume(
    meta: dict[str, Any],
    api_volume: Any,
    api_issue: Any,
    path: Path,
) -> None:
    m_vol = re.search(r"vol-(\d+)", str(path))
    path_vol: int | None = int(m_vol.group(1)) if m_vol else None

    if path_vol is not None:
        meta["volume"] = path_vol
    elif api_volume and not meta.get("volume"):
        meta["volume"] = _coerce_int_or_str(api_volume)

    if api_issue and not meta.get("issue"):
        issue_str = str(api_issue).strip()
        m_comp = _COMPOSITE_ISSUE_RE.match(issue_str)
        if m_comp:
            first_num = int(m_comp.group(1))
            second_num = int(m_comp.group(2))
            current_vol = meta.get("volume")
            if current_vol is not None and str(current_vol) == str(second_num):
                meta["issue"] = first_num
            else:
                meta["issue"] = issue_str
        else:
            meta["issue"] = _coerce_int_or_str(issue_str)


def _enrich_from_zenodo(meta: dict[str, Any], recid: str, path: Path) -> None:
    url = f"https://zenodo.org/api/records/{recid}"
    print(f"Buscando metadados no Zenodo (record {recid})...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    z_meta: dict[str, Any] = payload.get("metadata", {}) or {}

    if z_meta.get("title") and (not meta.get("title") or str(meta.get("title")).strip().lower() == "sem título"):
        meta["title"] = str(z_meta["title"]).strip()

    if z_meta.get("publication_date") and not meta.get("date"):
        meta["date"] = str(z_meta["publication_date"]).strip()

    z_journal = z_meta.get("journal") or {}
    if isinstance(z_journal, dict):
        if z_journal.get("title") and not meta.get("journal"):
            meta["journal"] = str(z_journal["title"]).strip()
        _resolve_issue_and_volume(meta, z_journal.get("volume"), z_journal.get("issue"), path)
        if z_journal.get("pages") and not meta.get("pages"):
            meta["pages"] = _normalize_pages(z_journal["pages"])
    else:
        _resolve_issue_and_volume(meta, None, None, path)

    if z_meta.get("creators") and not meta.get("authors"):
        authors: list[dict[str, str]] = []
        for creator in z_meta["creators"]:
            name = str(creator.get("name", "")).strip()
            if "," in name:
                parts = [p.strip() for p in name.split(",", maxsplit=1)]
                name = f"{parts[1]} {parts[0]}".strip()
            entry: dict[str, str] = {"name": name}
            if creator.get("orcid"):
                entry["orcid"] = str(creator["orcid"]).split("/")[-1].strip()
            if creator.get("affiliation"):
                entry["affiliation"] = str(creator["affiliation"]).strip()
            if entry["name"]:
                authors.append(entry)
        if authors:
            meta["authors"] = authors
            meta.pop("author", None)

    z_license = z_meta.get("license")
    if isinstance(z_license, dict) and z_license.get("id") and not meta.get("license"):
        meta["license"] = str(z_license["id"]).upper().replace("-", " ")


def _enrich_from_crossref(meta: dict[str, Any], doi: str, path: Path) -> None:
    url = f"https://api.crossref.org/works/{doi}"
    print(f"Buscando metadados para o DOI: {doi} via Crossref...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data: dict[str, Any] = response.json()["message"]

    container = data.get("container-title") or data.get("short-container-title")
    if container and not meta.get("journal"):
        journal_name = container[0] if isinstance(container, list) else str(container)
        if str(journal_name).strip():
            meta["journal"] = str(journal_name).strip()

    _resolve_issue_and_volume(meta, data.get("volume"), data.get("issue"), path)

    if data.get("page") and not meta.get("pages"):
        meta["pages"] = _normalize_pages(data["page"])

    issns = data.get("ISSN") or []
    if issns and not meta.get("e_issn"):
        meta["e_issn"] = str(issns[0]).strip()

    if data.get("author") and not meta.get("authors"):
        authors: list[dict[str, str]] = []
        for item in data["author"]:
            full_name = f"{item.get('given', '')} {item.get('family', '')}".strip()
            author_dict: dict[str, str] = {"name": full_name}
            if item.get("ORCID"):
                author_dict["orcid"] = str(item["ORCID"]).split("/")[-1].strip()
            affs = item.get("affiliation") or []
            if affs and isinstance(affs, list) and affs[0].get("name"):
                author_dict["affiliation"] = str(affs[0]["name"]).strip()
            if author_dict["name"]:
                authors.append(author_dict)
        if authors:
            meta["authors"] = authors
            meta.pop("author", None)


def enrich_metadata(filepath: str | Path) -> dict[str, Any] | None:
    """Enriquece metadados YAML do Markdown consultando Zenodo ou Crossref via DOI."""
    path = Path(filepath)
    if not path.exists():
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return None

    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)", content, re.DOTALL)
    if not match:
        print("Frontmatter YAML não encontrado no arquivo.")
        return None

    fm_text, body = match.group(1), match.group(2)
    try:
        loaded = yaml.safe_load(fm_text) or {}
        if not isinstance(loaded, dict):
            print("Frontmatter YAML inválido: esperava mapeamento de chaves.")
            return None
        meta: dict[str, Any] = loaded
    except yaml.YAMLError as exc:
        print(f"Erro ao parsear YAML: {exc}")
        return None

    raw_doi = meta.get("DOI") or meta.get("doi")
    if not raw_doi:
        print("Nenhum DOI encontrado no Frontmatter.")
        return None

    doi = _normalize_doi(str(raw_doi))
    try:
        zenodo_match = _ZENODO_DOI_RE.match(doi)
        if zenodo_match:
            _enrich_from_zenodo(meta, zenodo_match.group(1), path)
        else:
            _enrich_from_crossref(meta, doi, path)

        new_fm_text = yaml.dump(meta, sort_keys=False, allow_unicode=True)
        new_content = f"---\n{new_fm_text}---\n{body}"
        path.write_text(new_content, encoding="utf-8")
        print("✅ Metadados enriquecidos com sucesso!")
        return meta
    except requests.RequestException as exc:
        print(f"Erro ao buscar metadados na API: {exc}")
        return None
    except Exception as exc:
        print(f"Ocorreu um erro ao enriquecer metadados: {exc}")
        return None
