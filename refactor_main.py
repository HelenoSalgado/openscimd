import re

with open('main.py', 'r') as f:
    content = f.read()

# Comment out global imports except indexer
content = re.sub(r'^(from scripts\.(assets|covers|html2md|ai_cover|validator|text_tools|enricher) import .*)$', r'# \1', content, flags=re.MULTILINE)

# Inject convert_assets
content = re.sub(
    r'(def build_assets\(\):\n    """Converte e redimensiona os assets de imagens."""\n)',
    r'\1    from scripts.assets import convert_assets\n',
    content
)

# Inject convert_covers
content = re.sub(
    r'(def build_covers\(.*?\):\n    """Converte e redimensiona capas de livros."""\n)',
    r'\1    from scripts.covers import convert_covers\n',
    content, flags=re.DOTALL
)

# Inject inject_cover_text
content = re.sub(
    r'(def inject_text\(.*?\):\n    """Injeta texto em capas brutas \(tipografia\)."""\n)',
    r'\1    from scripts.covers import inject_cover_text\n',
    content, flags=re.DOTALL
)

# Inject convert_html_to_md
content = re.sub(
    r'(def html_to_md\(.*?\):\n    """Converte HTML exportado para Markdown com Frontmatter YAML."""\n)',
    r'\1    from scripts.html2md import convert_html_to_md\n',
    content, flags=re.DOTALL
)

# Inject generate_cover
content = re.sub(
    r'(def ai_cover\(.*?\):\n    """Gera uma arte de capa com IA \(gemini ou openai\)."""\n)',
    r'\1    from scripts.ai_cover import generate_cover\n',
    content, flags=re.DOTALL
)

# Inject validate_articles
content = re.sub(
    r'(def validate\(\):\n    """Valida formato e metadados de artigos MD."""\n)',
    r'\1    from scripts.validator import validate_articles\n',
    content
)

# Inject converter_versiculos
content = re.sub(
    r'(def verses\(.*?\):\n    """Converte formatação de versículos bíblicos."""\n)',
    r'\1    from scripts.text_tools import converter_versiculos\n',
    content, flags=re.DOTALL
)

# Inject spellcheck
content = re.sub(
    r'(def spell_check\(.*?\):\n    """Aplica spellcheck num arquivo md usando as regras."""\n)',
    r'\1    from scripts.text_tools import spellcheck\n',
    content, flags=re.DOTALL
)

# Inject normalize_biblical_refs
content = re.sub(
    r'(def normalize_refs\(.*?\):\n    """Normaliza referências bíblicas."""\n)',
    r'\1    from scripts.text_tools import normalize_biblical_refs\n',
    content, flags=re.DOTALL
)

# Inject enrich_metadata
content = re.sub(
    r'(def enrich_metadata_cmd\(.*?\):\n    """Enriquece o frontmatter de um documento."""\n)',
    r'\1    from scripts.enricher import enrich_metadata\n',
    content, flags=re.DOTALL
)

with open('main.py', 'w') as f:
    f.write(content)
