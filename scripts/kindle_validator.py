#!/usr/bin/env python3
"""Validador de conformidade editorial e técnica para Amazon Kindle Direct Publishing (KDP)."""

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class KindleValidationResult:
    """Resultado da validação de um arquivo EPUB para Amazon KDP."""

    epub_path: Path
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.infos.append(message)


class SimpleHTMLInspector(HTMLParser):
    """Extrator leve de IDs, links e imagens em arquivos XHTML/HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.declared_ids: Set[str] = set()
        self.image_sources: List[str] = []
        self.internal_links: List[str] = []
        self.has_scripts: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}

        # Coletar IDs declarados para validação de âncoras
        if "id" in attr_dict:
            self.declared_ids.add(attr_dict["id"])
        if "name" in attr_dict and tag.lower() == "a":
            self.declared_ids.add(attr_dict["name"])

        # Detectar scripts não permitidos no KDP
        if tag.lower() == "script":
            self.has_scripts = True

        # Imagens
        if tag.lower() in ("img", "image"):
            src = attr_dict.get("src") or attr_dict.get("xlink:href") or attr_dict.get("href")
            if src:
                self.image_sources.append(src)

        # Links internos
        if tag.lower() == "a":
            href = attr_dict.get("href")
            if href:
                self.internal_links.append(href)


class KindleValidator:
    """Valida a conformidade de arquivos EPUB 3 segundo as especificações do Amazon Kindle (KDP)."""

    NAMESPACES = {
        "container": "urn:oasis:names:tc:opendocument:xmlns:container",
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def __init__(self, epub_path: str | Path) -> None:
        self.epub_path = Path(epub_path).resolve()

    def validate(self) -> KindleValidationResult:
        """Executa a bateria completa de testes de validação para KDP."""
        result = KindleValidationResult(epub_path=self.epub_path)

        if not self.epub_path.exists():
            result.add_error(f"Arquivo EPUB não encontrado: {self.epub_path}")
            return result

        if not self.epub_path.is_file() or self.epub_path.suffix.lower() != ".epub":
            result.add_error(f"Caminho não é um arquivo .epub válido: {self.epub_path}")
            return result

        try:
            with zipfile.ZipFile(self.epub_path, "r") as zf:
                self._check_mimetype(zf, result)
                opf_path = self._check_container(zf, result)
                if opf_path:
                    self._check_package_opf(zf, opf_path, result)
        except zipfile.BadZipFile:
            result.add_error("Arquivo EPUB corrompido ou formato ZIP inválido.")
        except Exception as e:
            result.add_error(f"Erro inesperado durante a inspeção: {str(e)}")

        return result

    def _check_mimetype(self, zf: zipfile.ZipFile, result: KindleValidationResult) -> None:
        """Verifica os requisitos rigorosos do arquivo mimetype exigidos pelo KDP/IDPF."""
        infolist = zf.infolist()
        if not infolist:
            result.add_error("O arquivo EPUB está vazio.")
            return

        first_file = infolist[0]
        if first_file.filename != "mimetype":
            result.add_error(
                f"O primeiro arquivo no pacote deve ser 'mimetype', mas foi encontrado '{first_file.filename}'."
            )

        if first_file.compress_type != zipfile.ZIP_STORED:
            result.add_error("O arquivo 'mimetype' deve ser armazenado sem compressão (ZIP_STORED).")

        mimetype_content = zf.read("mimetype")
        if mimetype_content != b"application/epub+zip":
            result.add_error(
                f"Conteúdo do 'mimetype' inválido: esperado 'application/epub+zip', obtido {mimetype_content!r}."
            )
        else:
            result.add_info("Mimetype em conformidade IDPF/Kindle (application/epub+zip não comprimido).")

    def _check_container(self, zf: zipfile.ZipFile, result: KindleValidationResult) -> Optional[str]:
        """Verifica META-INF/container.xml e resolve o caminho do arquivo OPF."""
        container_path = "META-INF/container.xml"
        if container_path not in zf.namelist():
            result.add_error(f"Arquivo obrigatório '{container_path}' não foi encontrado no EPUB.")
            return None

        try:
            xml_data = zf.read(container_path)
            root = ET.fromstring(xml_data)
            rootfile = root.find(".//container:rootfile", self.NAMESPACES)
            if rootfile is None:
                # Tentar sem namespace
                rootfile = root.find(".//rootfile")

            if rootfile is None or "full-path" not in rootfile.attrib:
                result.add_error("Elemento <rootfile> com atributo 'full-path' ausente em META-INF/container.xml.")
                return None

            opf_path = rootfile.attrib["full-path"]
            if opf_path not in zf.namelist():
                result.add_error(f"Arquivo OPF indicado no container não existe no pacote: '{opf_path}'.")
                return None

            result.add_info(f"Container e arquivo OPF identificados com sucesso: '{opf_path}'.")
            return opf_path
        except ET.ParseError as e:
            result.add_error(f"Erro de sintaxe XML em '{container_path}': {str(e)}")
            return None

    def _check_package_opf(self, zf: zipfile.ZipFile, opf_path: str, result: KindleValidationResult) -> None:
        """Inspeciona metadados, manifesto, spine e recursos referenciados no arquivo OPF."""
        try:
            opf_data = zf.read(opf_path)
            root = ET.fromstring(opf_data)
        except ET.ParseError as e:
            result.add_error(f"Erro de sintaxe XML no arquivo OPF '{opf_path}': {str(e)}")
            return

        opf_dir = Path(opf_path).parent

        # 1. Metadados do Dublin Core
        self._validate_metadata(root, result)

        # 2. Manifesto
        manifest_items, nav_found, ncx_found, cover_found = self._validate_manifest(
            zf, root, opf_dir, result
        )

        # 3. Spine
        self._validate_spine(root, manifest_items, result)

        # 4. Navegação
        if not nav_found:
            result.add_error("Documento de navegação EPUB 3 (properties='nav') não encontrado no manifesto.")
        else:
            result.add_info("Navegação EPUB 3 (Nav Doc) identificada.")

        if not ncx_found:
            result.add_warning(
                "Tabela de navegação legada (toc.ncx) não encontrada. Recomendada para máxima retrocompatibilidade com Kindles e-ink antigos."
            )
        else:
            result.add_info("Tabela de navegação NCX de compatibilidade identificada.")

        # 5. Capa
        if not cover_found:
            result.add_warning(
                "Nenhuma imagem de capa explicitamente identificada com properties='cover-image' ou <meta name='cover'>."
            )
        else:
            result.add_info("Imagem de capa canônica identificada no pacote.")

        # 6. Integridade de links e recursos nos XHTML do spine
        self._validate_content_xhtml(zf, root, opf_dir, manifest_items, result)

    def _validate_metadata(self, root: ET.Element, result: KindleValidationResult) -> None:
        """Valida a presença de metadados exigidos pela Amazon KDP."""
        metadata_el = root.find(".//opf:metadata", self.NAMESPACES)
        if metadata_el is None:
            metadata_el = root.find(".//metadata")

        if metadata_el is None:
            result.add_error("Elemento <metadata> ausente no arquivo OPF.")
            return

        # dc:title
        title_el = metadata_el.find(".//dc:title", self.NAMESPACES)
        if title_el is None:
            title_el = metadata_el.find(".//{http://purl.org/dc/elements/1.1/}title")
        if title_el is None or not (title_el.text or "").strip():
            result.add_error("Metadado mandatório <dc:title> está ausente ou vazio.")
        else:
            result.metadata["title"] = title_el.text.strip()

        # dc:language
        lang_el = metadata_el.find(".//dc:language", self.NAMESPACES)
        if lang_el is None:
            lang_el = metadata_el.find(".//{http://purl.org/dc/elements/1.1/}language")
        if lang_el is None or not (lang_el.text or "").strip():
            result.add_error("Metadado mandatório <dc:language> está ausente ou vazio.")
        else:
            lang_val = lang_el.text.strip()
            result.metadata["language"] = lang_val
            if not re.match(r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]+)?$", lang_val):
                result.add_warning(f"Formato de idioma <dc:language>'{lang_val}' pode não ser reconhecido pelo KDP.")

        # dc:creator
        creator_el = metadata_el.find(".//dc:creator", self.NAMESPACES)
        if creator_el is None:
            creator_el = metadata_el.find(".//{http://purl.org/dc/elements/1.1/}creator")
        if creator_el is None or not (creator_el.text or "").strip():
            result.add_warning("Metadado <dc:creator> (autor) não foi especificado no OPF.")
        else:
            result.metadata["creator"] = creator_el.text.strip()

        # dc:identifier
        id_el = metadata_el.find(".//dc:identifier", self.NAMESPACES)
        if id_el is None:
            id_el = metadata_el.find(".//{http://purl.org/dc/elements/1.1/}identifier")
        if id_el is None or not (id_el.text or "").strip():
            result.add_error("Metadado mandatório <dc:identifier> está ausente ou vazio.")
        else:
            result.metadata["identifier"] = id_el.text.strip()

    def _validate_manifest(
        self, zf: zipfile.ZipFile, root: ET.Element, opf_dir: Path, result: KindleValidationResult
    ) -> Tuple[Dict[str, Dict[str, str]], bool, bool, bool]:
        """Valida o manifesto e a existência de todos os arquivos referenciados."""
        manifest_items: Dict[str, Dict[str, str]] = {}
        nav_found = False
        ncx_found = False
        cover_found = False

        manifest_el = root.find(".//opf:manifest", self.NAMESPACES)
        if manifest_el is None:
            manifest_el = root.find(".//manifest")

        if manifest_el is None:
            result.add_error("Elemento <manifest> ausente no arquivo OPF.")
            return manifest_items, nav_found, ncx_found, cover_found

        all_zip_names = set(zf.namelist())

        for item in manifest_el.findall(".//opf:item", self.NAMESPACES) or manifest_el.findall(".//item"):
            item_id = item.attrib.get("id")
            href = item.attrib.get("href")
            media_type = item.attrib.get("media-type", "")
            properties = item.attrib.get("properties", "").split()

            if not item_id or not href:
                result.add_error("Item de manifesto encontrado sem 'id' ou 'href'.")
                continue

            # Resolver caminho relativo dentro do zip normalizado
            raw_full_path = (opf_dir / urllib.parse.unquote(href)).as_posix()
            item_full_path = os.path.normpath(raw_full_path)
            if item_full_path.startswith("./"):
                item_full_path = item_full_path[2:]

            manifest_items[item_id] = {
                "href": href,
                "full_path": item_full_path,
                "media_type": media_type,
                "properties": " ".join(properties),
            }

            if item_full_path not in all_zip_names:
                result.add_error(f"Arquivo listado no manifesto não existe no pacote EPUB: '{item_full_path}'.")

            if "nav" in properties:
                nav_found = True

            if media_type == "application/x-dtbncx+xml" or href.endswith(".ncx"):
                ncx_found = True

            if "cover-image" in properties:
                cover_found = True

        # Verificar também meta cover em metadata
        if not cover_found:
            for meta in root.findall(".//opf:meta", self.NAMESPACES) or root.findall(".//meta"):
                if meta.attrib.get("name") == "cover":
                    cover_id = meta.attrib.get("content")
                    if cover_id and cover_id in manifest_items:
                        cover_found = True
                        break

        return manifest_items, nav_found, ncx_found, cover_found

    def _validate_spine(
        self, root: ET.Element, manifest_items: Dict[str, Dict[str, str]], result: KindleValidationResult
    ) -> None:
        """Valida os elementos do spine e sua correspondência no manifesto."""
        spine_el = root.find(".//opf:spine", self.NAMESPACES)
        if spine_el is None:
            spine_el = root.find(".//spine")

        if spine_el is None:
            result.add_error("Elemento <spine> ausente no arquivo OPF.")
            return

        itemrefs = spine_el.findall(".//opf:itemref", self.NAMESPACES) or spine_el.findall(".//itemref")
        if not itemrefs:
            result.add_error("O <spine> do EPUB está vazio; nenhum capítulo ou documento de leitura foi definido.")
            return

        for itemref in itemrefs:
            idref = itemref.attrib.get("idref")
            if not idref:
                result.add_error("Elemento <itemref> sem atributo 'idref'.")
            elif idref not in manifest_items:
                result.add_error(f"Itemref com idref='{idref}' não existe no <manifest>.")

    def _validate_content_xhtml(
        self,
        zf: zipfile.ZipFile,
        root: ET.Element,
        opf_dir: Path,
        manifest_items: Dict[str, Dict[str, str]],
        result: KindleValidationResult,
    ) -> None:
        """Inspeciona os arquivos XHTML do livro em busca de imagens quebradas, scripts e âncoras locais."""
        spine_el = root.find(".//opf:spine", self.NAMESPACES) or root.find(".//spine")
        if spine_el is None:
            return

        all_zip_names = set(zf.namelist())
        doc_declared_ids: Dict[str, Set[str]] = {}
        doc_links: Dict[str, List[Tuple[str, str]]] = {}  # full_path -> [(href, doc_relative)]

        # Primeira passagem: inspecionar recursos e coletar IDs
        for itemref in spine_el.findall(".//opf:itemref", self.NAMESPACES) or spine_el.findall(".//itemref"):
            idref = itemref.attrib.get("idref")
            if not idref or idref not in manifest_items:
                continue

            doc_info = manifest_items[idref]
            full_path = doc_info["full_path"]

            if full_path not in all_zip_names:
                continue

            try:
                xhtml_content = zf.read(full_path).decode("utf-8")
                inspector = SimpleHTMLInspector()
                inspector.feed(xhtml_content)

                if inspector.has_scripts:
                    result.add_warning(
                        f"Tag <script> encontrada em '{full_path}'. O KDP remove ou rejeita scripts em livros convencionais."
                    )

                doc_declared_ids[full_path] = inspector.declared_ids
                doc_dir = Path(full_path).parent

                # Validar imagens referenciadas
                for img_src in inspector.image_sources:
                    if img_src.startswith(("http://", "https://", "data:")):
                        result.add_warning(
                            f"Imagem com referência externa ou base64 encontrada em '{full_path}': {img_src}"
                        )
                        continue

                    # Resolver caminho da imagem
                    clean_src = urllib.parse.unquote(img_src.split("#")[0].split("?")[0])
                    resolved_img = os.path.normpath((doc_dir / clean_src).as_posix())
                    if resolved_img.startswith("./"):
                        resolved_img = resolved_img[2:]

                    if resolved_img not in all_zip_names:
                        result.add_error(f"Imagem referenciada em '{full_path}' não foi encontrada: '{clean_src}'.")

                # Guardar links internos para validação na segunda passagem
                for href in inspector.internal_links:
                    if href.startswith(("http://", "https://", "mailto:")):
                        continue
                    doc_links.setdefault(full_path, []).append((href, doc_dir.as_posix()))

            except Exception as e:
                result.add_warning(f"Não foi possível analisar detalhadamente '{full_path}': {e}")

        # Segunda passagem: validar âncoras e links internos
        for source_path, links in doc_links.items():
            source_dir = Path(source_path).parent
            for href, _ in links:
                if href.startswith("#"):
                    anchor = href[1:]
                    if anchor and anchor not in doc_declared_ids.get(source_path, set()):
                        result.add_warning(
                            f"Link interno #{anchor} em '{source_path}' aponta para um ID não encontrado no próprio documento."
                        )
                else:
                    parts = href.split("#", 1)
                    target_file = parts[0]
                    anchor = parts[1] if len(parts) > 1 else None

                    target_full = os.path.normpath((source_dir / urllib.parse.unquote(target_file)).as_posix())
                    if target_full.startswith("./"):
                        target_full = target_full[2:]

                    if target_full not in all_zip_names:
                        result.add_error(
                            f"Link interno em '{source_path}' aponta para arquivo inexistente: '{target_file}'."
                        )
                    elif anchor and target_full in doc_declared_ids:
                        if anchor not in doc_declared_ids[target_full]:
                            result.add_warning(
                                f"Link interno em '{source_path}' aponta para âncora inexistente #{anchor} em '{target_file}'."
                            )


def validate_kindle_epub(epub_path: str | Path) -> KindleValidationResult:
    """Função utilitária de conveniência para validação rápida de conformidade Amazon Kindle."""
    validator = KindleValidator(epub_path)
    return validator.validate()
