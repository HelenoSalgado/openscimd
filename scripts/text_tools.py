from __future__ import annotations

import os
import re
from pathlib import Path

from scripts.biblical_books import iter_biblical_reference_matches
from scripts.spellchecker.masker import MarkdownMasker


def converter_versiculos(input_path: str | Path, output_path: str | Path) -> None:
    """Converte números no início da linha para formato sobrescrito."""
    superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

    with open(input_path, encoding="utf-8") as f_in:
        lines = f_in.readlines()

    with open(output_path, "w", encoding="utf-8") as f_out:
        for line in lines:
            match = re.match(r"^(\d+)\.\s*(.*)", line)
            if match:
                num_str = match.group(1)
                rest_of_line = match.group(2)
                super_num = num_str.translate(superscript_map)
                f_out.write(f"{super_num} {rest_of_line}\n")
            else:
                f_out.write(line)

    print(f"Conversão de versículos concluída. Escrito em: {output_path}")


def normalize_biblical_refs(
    filepath: str | Path,
    target_sep: str = ".",
    regex_pattern: str | None = None,
    replacement: str | None = None,
    canonical_abbrev: bool = True,
    force_abbrev: bool = False,
    normalize_ranges: bool = True,
) -> int:
    """Padroniza referências bíblicas apenas no texto de prosa (ignorando YAML, código e links).

    Preserva nomes por extenso vs abreviações quando canonical_abbrev=True e force_abbrev=False,
    corrigindo apenas variantes fora do padrão (ex.: HB -> Hb, Mat. -> Mt, 1Coríntios -> 1 Coríntios).
    """
    path_str = str(filepath)
    if not os.path.exists(path_str):
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return 0

    with open(path_str, encoding="utf-8") as f:
        content = f.read()

    masked = MarkdownMasker.mask(content)
    replacements: list[tuple[int, int, str]] = []

    if regex_pattern:
        if replacement is None:
            print("Erro: 'replacement' é obrigatório quando 'regex_pattern' é informado.")
            return 0
        try:
            compiled = re.compile(regex_pattern)
        except re.error as e:
            print(f"Erro na expressão regular: {e}")
            return 0

        for m in compiled.finditer(masked):
            new_str = m.expand(replacement)
            if new_str != m.group(0):
                replacements.append((m.start(), m.end(), new_str))
    else:
        for ref_match in iter_biblical_reference_matches(
            masked,
            target_sep=target_sep,
            canonical_abbrev=canonical_abbrev,
            force_abbrev=force_abbrev,
            normalize_ranges=normalize_ranges,
        ):
            if not ref_match.is_canonical:
                replacements.append((ref_match.start, ref_match.end, ref_match.expected))

    if replacements:
        updated = content
        for start, end, new_text in sorted(replacements, key=lambda x: x[0], reverse=True):
            updated = updated[:start] + new_text + updated[end:]

        with open(path_str, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"✅ Referências normalizadas: {len(replacements)} substituições realizadas em '{filepath}'.")
    else:
        print("Nenhuma correspondência encontrada para o padrão no arquivo.")

    return len(replacements)


class Colors:
    """ANSI color codes for terminal formatting."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


def spellcheck(filepath: str | Path, dict_path: str | Path | None = None) -> None:
    """Revisor ortográfico para arcaísmos (delega para scripts.spellchecker)."""
    from scripts.spellchecker import review_path

    review_path(filepath, dict_path=dict_path)
