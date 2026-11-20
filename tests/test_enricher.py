"""Testes unitários para enriquecimento de metadados via Crossref e Zenodo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.enricher import enrich_metadata


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_enrich_crossref_uses_container_title_and_protects_vol_from_composite_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    art_dir = tmp_path / "data" / "review" / "articles" / "peitho" / "vol-2"
    art_dir.mkdir(parents=True)
    art = art_dir / "estudo.md"
    art.write_text(
        "---\n"
        'title: "Estudo sobre Sócrates"\n'
        'DOI: "10.14746/pea.2011.1.12"\n'
        "---\n\n"
        "Corpo do artigo.\n",
        encoding="utf-8",
    )

    def fake_get(url: str, timeout: int = 10) -> _FakeResponse:
        assert "api.crossref.org/works/10.14746/pea.2011.1.12" in url
        return _FakeResponse(
            {
                "message": {
                    "publisher": "Editora Genérica Ltda",
                    "container-title": ["Peitho / Examina Antiqua"],
                    "volume": "1",
                    "issue": "1(2)",
                    "page": "183-190",
                    "ISSN": ["2082-7539"],
                    "author": [
                        {
                            "given": "Dorota",
                            "family": "Tymura",
                            "ORCID": "https://orcid.org/0000-0001-2345-6789",
                            "affiliation": [{"name": "Universidade de Lublin"}],
                        }
                    ],
                }
            }
        )

    monkeypatch.setattr("scripts.enricher.requests.get", fake_get)
    meta = enrich_metadata(art)

    assert meta is not None
    assert meta["journal"] == "Peitho / Examina Antiqua"
    assert meta["volume"] == 2
    assert meta["issue"] == 1
    assert meta["pages"] == "183–190"
    assert meta["e_issn"] == "2082-7539"
    assert meta["authors"][0]["name"] == "Dorota Tymura"
    assert meta["authors"][0]["orcid"] == "0000-0001-2345-6789"
    assert meta["authors"][0]["affiliation"] == "Universidade de Lublin"


def test_enrich_zenodo_extracts_creators_and_journal_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    art_dir = tmp_path / "data" / "review" / "articles" / "avulsos" / "vol-1"
    art_dir.mkdir(parents=True)
    art = art_dir / "ensaio.md"
    art.write_text(
        "---\n"
        'title: "Sem Título"\n'
        'DOI: "10.5281/zenodo.987654"\n'
        "---\n\n"
        "Corpo do ensaio.\n",
        encoding="utf-8",
    )

    def fake_get(url: str, timeout: int = 10) -> _FakeResponse:
        assert url == "https://zenodo.org/api/records/987654"
        return _FakeResponse(
            {
                "metadata": {
                    "title": "Ensaio sobre Lógica",
                    "publication_date": "2025-11-20",
                    "license": {"id": "cc-by-4.0"},
                    "journal": {
                        "title": "Revista Lógica",
                        "volume": "1",
                        "issue": "3",
                        "pages": "10-25",
                    },
                    "creators": [
                        {
                            "name": "Konishi, Hiroko",
                            "orcid": "0000-0002-0000-0001",
                            "affiliation": "Instituto de IA",
                        }
                    ],
                }
            }
        )

    monkeypatch.setattr("scripts.enricher.requests.get", fake_get)
    meta = enrich_metadata(art)

    assert meta is not None
    assert meta["title"] == "Ensaio sobre Lógica"
    assert meta["date"] == "2025-11-20"
    assert meta["journal"] == "Revista Lógica"
    assert meta["volume"] == 1
    assert meta["issue"] == 3
    assert meta["pages"] == "10–25"
    assert meta["license"] == "CC BY 4.0"
    assert meta["authors"][0]["name"] == "Hiroko Konishi"
