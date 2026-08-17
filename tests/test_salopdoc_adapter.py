from pathlib import Path
import pytest
from scripts.salopdoc_adapter import (
    get_default_config,
    clean_markdown_file,
    import_pdf,
    batch_import,
)


def test_get_default_config(tmp_path):
    # Test loading root config
    config = get_default_config()
    assert config is not None
    assert str(config.paths.input_dir).endswith("data/raw")
    assert str(config.paths.output_dir).endswith("data/draft")
    assert config.date.format == "%Y-%m-%d"
    assert config.frontmatter.enabled is True


def test_clean_markdown_file(tmp_path):
    input_file = tmp_path / "legacy_article.md"
    output_file = tmp_path / "cleaned_article.md"
    
    # Text with unnormalized quotes and messy headings
    raw_text = """# Title
## Section 1
"This is an article with quotes" and 'single quotes'.

### Subheading
Some text here.
"""
    input_file.write_text(raw_text, encoding="utf-8")
    
    res = clean_markdown_file(input_file, output_file)
    assert res.exists()
    
    cleaned_content = output_file.read_text(encoding="utf-8")
    assert "Title" in cleaned_content
    assert res == output_file


def test_import_pdf_file_not_found(tmp_path):
    non_existent = tmp_path / "non_existent.pdf"
    with pytest.raises(FileNotFoundError):
        import_pdf(non_existent)


def test_batch_import_empty_or_non_existent(tmp_path):
    non_existent_dir = tmp_path / "no_such_dir"
    with pytest.raises(FileNotFoundError):
        batch_import(input_dir=non_existent_dir)
        
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    out_dir = tmp_path / "output_dir"
    
    results = batch_import(input_dir=empty_dir, output_dir=out_dir)
    assert results == []
