import json
from pathlib import Path
from typing import Any, List, Optional

CATEGORIES_FILE = Path(__file__).resolve().parent / "data" / "categories.json"

_CACHED_CATEGORIES: Optional[List[str]] = None


def load_allowed_categories() -> List[str]:
    """Carrega a lista pré-aprovada de categorias canônicas (disciplinas generalistas)."""
    global _CACHED_CATEGORIES
    if _CACHED_CATEGORIES is not None:
        return _CACHED_CATEGORIES

    if not CATEGORIES_FILE.exists():
        raise FileNotFoundError(f"Arquivo de categorias não encontrado em: {CATEGORIES_FILE}")

    with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {CATEGORIES_FILE}: esperava uma lista JSON.")

    _CACHED_CATEGORIES = [str(cat).strip() for cat in data if str(cat).strip()]
    return _CACHED_CATEGORIES


def normalize_categories(categories: List[str]) -> List[str]:
    """Remove duplicatas, aplica strip e ordena alfabeticamente uma lista de categorias."""
    if not categories:
        return []
    cleaned = list({str(c).strip() for c in categories if str(c).strip()})
    return sorted(cleaned)


def validate_categories(categories_val: Any) -> List[str]:
    """Valida a integridade da chave categories em relação à taxonomia pré-aprovada.

    Retorna uma lista de mensagens de erro encontradas (vazia caso seja válido).
    Critérios verificados:
      1. Presença obrigatória e não vazia.
      2. Tipo deve ser estritamente uma lista de strings.
      3. Cada categoria deve pertencer à lista canônica pré-aprovada.
      4. Ausência de elementos duplicados.
      5. Ordenação alfabética obrigatória.
    """
    errors: List[str] = []

    if categories_val is None:
        errors.append('Campo obrigatório "categories" está ausente.')
        return errors

    if not isinstance(categories_val, list):
        errors.append('Campo "categories" deve ser uma lista (array) de strings no YAML.')
        return errors

    if len(categories_val) == 0:
        errors.append('Campo "categories" não pode ser uma lista vazia.')
        return errors

    allowed = set(load_allowed_categories())
    seen = set()
    has_duplicates = False

    for item in categories_val:
        if not isinstance(item, str) or not item.strip():
            errors.append(f'Elemento inválido em "categories": "{item}". Esperado texto não vazio.')
            continue

        item_clean = item.strip()
        if item_clean in seen:
            has_duplicates = True
        seen.add(item_clean)

        if item_clean not in allowed:
            errors.append(
                f'Categoria inválida ou composta: "{item_clean}". '
                f'Use apenas disciplinas generalistas pré-aprovadas. '
                f'Detalhes específicos, correntes e cronologias pertencem à chave "keywords".'
            )

    if has_duplicates:
        errors.append('A chave "categories" contém elementos duplicados.')

    # Validação de ordenação alfabética
    string_items = [str(x).strip() for x in categories_val if isinstance(x, str)]
    if string_items and string_items != sorted(string_items):
        errors.append(
            f'A lista "categories" não está ordenada alfabeticamente. '
            f'Ordem atual: {string_items}; Ordem esperada: {sorted(string_items)}.'
        )

    return errors
