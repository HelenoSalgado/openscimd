from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATEGORIES_FILE = Path(__file__).resolve().parent / "data" / "categories.json"

_CACHED_CATEGORIES: list[str] | None = None


def load_allowed_categories() -> list[str]:
    """Carrega a lista pré-aprovada de categorias canônicas (disciplinas generalistas)."""
    global _CACHED_CATEGORIES
    if _CACHED_CATEGORIES is not None:
        return _CACHED_CATEGORIES

    if not CATEGORIES_FILE.exists():
        raise FileNotFoundError(f"Arquivo de categorias não encontrado em: {CATEGORIES_FILE}")

    with open(CATEGORIES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {CATEGORIES_FILE}: esperava uma lista JSON.")

    _CACHED_CATEGORIES = [str(cat).strip() for cat in data if str(cat).strip()]
    return _CACHED_CATEGORIES


def normalize_categories(categories: list[str]) -> list[str]:
    """Remove duplicatas, aplica strip e ordena alfabeticamente uma lista de categorias."""
    if not categories:
        return []
    cleaned = list({str(c).strip() for c in categories if str(c).strip()})
    return sorted(cleaned)


def validate_categories(categories_val: Any) -> list[str]:
    """Valida a integridade da chave categories em relação à taxonomia pré-aprovada.

    Retorna uma lista de mensagens de erro encontradas (vazia caso seja válido).
    Critérios verificados:
      1. Presença obrigatória e não vazia.
      2. Tipo deve ser estritamente uma lista de strings.
      3. Cada categoria deve pertencer à lista canônica pré-aprovada.
      4. Ausência de elementos duplicados.
      5. Ordenação alfabética obrigatória.
    """
    errors: list[str] = []

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
    seen: set[str] = set()
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
                "Use apenas disciplinas generalistas pré-aprovadas. "
                'Detalhes específicos, correntes e cronologias pertencem à chave "keywords".'
            )

    if has_duplicates:
        errors.append('A chave "categories" contém elementos duplicados.')

    string_items = [str(x).strip() for x in categories_val if isinstance(x, str)]
    if string_items and string_items != sorted(string_items):
        errors.append(
            f'A lista "categories" não está ordenada alfabeticamente. '
            f"Ordem atual: {string_items}; Ordem esperada: {sorted(string_items)}."
        )

    return errors


# Mapeamento oficial de disciplinas canônicas para a Classificação Decimal Universal (CDU / UDC)
CATEGORY_TO_UDC: dict[str, str] = {
    "Antropologia": "39",
    "Artes": "7",
    "Astronomia": "52",
    "Biologia": "57",
    "Computação": "004",
    "Direito": "34",
    "Economia": "33",
    "Educação": "37",
    "Filosofia": "1",
    "Física": "53",
    "Geografia": "91",
    "História": "94",
    "Linguística": "81",
    "Literatura": "82",
    "Matemática": "51",
    "Medicina": "61",
    "Música": "78",
    "Poesia": "82-1",
    "Política": "32",
    "Psicologia": "159.9",
    "Química": "54",
    "Sociologia": "316",
    "Teologia": "2",
}


def derive_udc_from_categories(categories: list[str] | None) -> str | None:
    """Deriva a notação CDU (UDC) a partir das categorias canônicas do documento.

    Se houver múltiplas categorias, combina os códigos com dois-pontos ':' segundo
    a sintaxe padrão da Classificação Decimal Universal.
    Exemplo: ['Filosofia', 'História'] -> '1:94'
    """
    if not categories:
        return None
    codes: list[str] = []
    for cat in sorted(categories):
        code = CATEGORY_TO_UDC.get(str(cat).strip())
        if code and code not in codes:
            codes.append(code)
    return ":".join(codes) if codes else None
