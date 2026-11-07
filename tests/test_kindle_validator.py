import io
import zipfile
from pathlib import Path
import pytest

from scripts.kindle_validator import KindleValidator, validate_kindle_epub


def test_kindle_validator_on_real_epub():
    epub_path = Path("dist/content/books/platao/apologia-de-socrates.epub")
    if not epub_path.exists():
        # Fallback se estiver na raiz
        epub_path = Path("dist/apologia-de-socrates.epub")
    if not epub_path.exists():
        pytest.skip("EPUB real da Apologia não gerado ainda.")

    result = validate_kindle_epub(epub_path)
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.metadata.get("title") == "Apologia de Sócrates"
    assert result.metadata.get("creator") == "Platão"
    assert result.metadata.get("language") == "pt-BR"
    assert "urn:uuid:" in result.metadata.get("identifier", "")


def test_kindle_validator_missing_file(tmp_path: Path):
    non_existent = tmp_path / "inexistente.epub"
    res = validate_kindle_epub(non_existent)
    assert res.is_valid is False
    assert any("não encontrado" in e for e in res.errors)


def test_kindle_validator_wrong_extension(tmp_path: Path):
    wrong_file = tmp_path / "livro.pdf"
    wrong_file.write_text("dummy")
    res = validate_kindle_epub(wrong_file)
    assert res.is_valid is False
    assert any("não é um arquivo .epub válido" in e for e in res.errors)


def test_kindle_validator_corrupt_zip(tmp_path: Path):
    corrupt_file = tmp_path / "corrupto.epub"
    corrupt_file.write_text("isto nao e um zip")
    res = validate_kindle_epub(corrupt_file)
    assert res.is_valid is False
    assert any("corrompido" in e.lower() or "zip" in e.lower() for e in res.errors)


def test_kindle_validator_bad_mimetype_order(tmp_path: Path):
    epub_file = tmp_path / "bad_order.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("outra_coisa.txt", "texto qualquer")
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("primeiro arquivo" in e for e in res.errors)


def test_kindle_validator_compressed_mimetype(tmp_path: Path):
    epub_file = tmp_path / "compressed_mime.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_DEFLATED)

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("sem compressão" in e for e in res.errors)


def test_kindle_validator_missing_container(tmp_path: Path):
    epub_file = tmp_path / "no_container.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("META-INF/container.xml" in e for e in res.errors)


def test_kindle_validator_missing_mandatory_metadata(tmp_path: Path):
    epub_file = tmp_path / "missing_meta.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                <rootfiles>
                    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
                </rootfiles>
            </container>""",
        )
        # OPF sem title nem identifier nem language
        zf.writestr(
            "content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
                <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                </metadata>
                <manifest>
                    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                </manifest>
                <spine>
                    <itemref idref="nav"/>
                </spine>
            </package>""",
        )
        zf.writestr("nav.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><body/></html>")

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("<dc:title>" in e for e in res.errors)
    assert any("<dc:language>" in e for e in res.errors)
    assert any("<dc:identifier>" in e for e in res.errors)


def test_kindle_validator_detects_broken_image(tmp_path: Path):
    epub_file = tmp_path / "broken_img.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                <rootfiles>
                    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
                </rootfiles>
            </container>""",
        )
        zf.writestr(
            "content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
                <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                    <dc:title>Livro Teste</dc:title>
                    <dc:language>pt-BR</dc:language>
                    <dc:identifier>urn:uuid:1234</dc:identifier>
                </metadata>
                <manifest>
                    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
                </manifest>
                <spine>
                    <itemref idref="nav"/>
                    <itemref idref="ch1"/>
                </spine>
            </package>""",
        )
        zf.writestr("nav.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><body/></html>")
        zf.writestr("ch1.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><body><img src='nao_existe.jpg'/></body></html>")

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("Imagem referenciada" in e and "nao_existe.jpg" in e for e in res.errors)


def test_kindle_validator_rejects_css_namespace_and_webp(tmp_path: Path):
    epub_file = tmp_path / "bad_css_and_webp.epub"
    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                <rootfiles>
                    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
                </rootfiles>
            </container>""",
        )
        zf.writestr(
            "content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
                <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                    <dc:title>Livro Teste</dc:title>
                    <dc:language>pt-BR</dc:language>
                    <dc:creator>Autor</dc:creator>
                    <dc:identifier>urn:uuid:1234</dc:identifier>
                </metadata>
                <manifest>
                    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                    <item id="css1" href="styles/stylesheet1.css" media-type="text/css"/>
                    <item id="img1" href="media/fig.webp" media-type="image/webp"/>
                    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
                </manifest>
                <spine>
                    <itemref idref="ch1"/>
                </spine>
            </package>""",
        )
        zf.writestr("nav.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Sumário</title></head><body/></html>")
        zf.writestr(
            "styles/stylesheet1.css",
            '@namespace epub "http://www.idpf.org/2007/ops";\nbody { margin: 0; }',
        )
        zf.writestr("media/fig.webp", b"RIFF....WEBP")
        zf.writestr("ch1.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>ch001.xhtml</title></head><body><h1></h1></body></html>")

    res = validate_kindle_epub(epub_file)
    assert res.is_valid is False
    assert any("@namespace" in e for e in res.errors)
    assert any("WebP" in e for e in res.errors)
    assert any("chXXX.xhtml" in w for w in res.warnings)
    assert any("Cabeçalho HTML vazio" in w for w in res.warnings)

