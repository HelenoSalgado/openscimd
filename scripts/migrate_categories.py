import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from scripts.categories import validate_categories, load_allowed_categories

BASE_DIR = Path(__file__).resolve().parent.parent

ARTICLES_MAP: Dict[str, Dict[str, Any]] = {
    "a-pratica-de-cantatas-e-concertos-no-culto-publico.md": {
        "categories": ["Música", "Teologia"],
        "add_keywords": ["Cantatas", "Música Sacra"],
        "extra": {"pages": "1-15", "volume": 1},
    },
    "alucinacoes-induzidas-e-o-loop-de-correcoes-falsas-em-llms.md": {
        "categories": ["Computação"],
        "add_keywords": ["Alucinações", "Grandes Modelos de Linguagem", "Inteligência Artificial", "LLMs"],
    },
    "o-legado-de-petrus-ramus-e-o-tradado-via-regia-ad-geometram.md": {
        "categories": ["História", "Matemática"],
        "add_keywords": ["Geometria", "História da Matemática", "Petrus Ramus"],
    },
    "as-margens-da-reforma-petrus-ramus-o-calvinismo-e-a-autonomia-do-saber-politico.md": {
        "categories": ["História", "Política"],
        "add_keywords": ["Ciência Política"],
    },
    "reformas-filosoficas-de-petrus-ramus.md": {
        "categories": ["Filosofia", "História"],
        "add_keywords": ["Lógica"],
    },
    "peter-ramus-importancia-na-retorica-e-ataque-a-cicero.md": {
        "categories": ["Filosofia", "Linguística"],
        "add_keywords": ["Retórica"],
    },
    "a-dimensao-juridica-politica-filosofica-e-religiosa-do-processo-e-da-execucao-de-socrates.md": {
        "categories": ["Direito", "Filosofia", "História"],
        "add_keywords": ["Estudos Clássicos", "Filosofia Antiga", "História do Direito"],
    },
    "de-cicerone-poeta-sine-ira-et-studio.md": {
        "categories": ["Filosofia", "Literatura"],
        "add_keywords": ["Estudos Clássicos", "Filosofia Antiga"],
    },
    "mais-um-volume-de-estudos-socraticos.md": {
        "categories": ["Filosofia"],
        "add_keywords": ["Estudos Clássicos", "Estudos Socráticos", "Filosofia Antiga"],
    },
    "o-metodo-de-aristoteles-para-a-compreensao-dos-primeiros-principios-das-coisas-naturais-na-fisica-i-1.md": {
        "categories": ["Filosofia", "Física"],
        "add_keywords": ["Aristotelismo", "Filosofia Antiga", "Física Aristotélica"],
    },
    "por-que-a-poesia-e-mais-filosofica-e-mais-nobre-do-que-a-historia.md": {
        "categories": ["Filosofia", "História", "Literatura"],
        "add_keywords": ["Filosofia Antiga", "Poética"],
    },
    "socrate-este-desconhecido.md": {
        "categories": ["Filosofia", "História"],
        "add_keywords": ["Estudos Socráticos", "Filosofia Antiga"],
    },
    "os-estoicos-sobre-o-bem-o-mal-e-os-indiferentes.md": {
        "categories": ["Filosofia"],
        "add_keywords": ["Estoicismo", "Filosofia Antiga", "Helenismo"],
    },
    "da-universidade-quinhentista-de-paris-para-o-mundo-curriculo-e-metodo-em-petrus-ramus.md": {
        "categories": ["Educação", "História"],
        "add_keywords": ["História da Educação"],
    },
    "universidades-surgimento-nacionalizacao-e-indicadores-de-internacionalizacao.md": {
        "categories": ["Educação", "História"],
        "add_keywords": ["Ensino Superior", "Universidades"],
    },
    "o-destino-eterno-dos-bebes-que-morrem-precocimente-e-das-pessoas-com-deficiencia-intelectual-severa.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Escatologia", "Salvação", "Soteriologia"],
    },
}

BOOKS_MAP: Dict[str, Dict[str, Any]] = {
    "soliloquios-livro-1.md": {
        "categories": ["Filosofia", "Teologia"],
        "add_keywords": ["Agostinho de Hipona", "Alma", "Patrística", "Solilóquios", "Verdade"],
    },
    "poetica.md": {
        "categories": ["Filosofia", "Literatura"],
        "add_keywords": ["Aristóteles", "Clássicos", "Mímesis", "Poética", "Tragédia"],
    },
    "a-palavra-de-deus.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Escola Vitorina", "Hermenêutica Medieval", "Hugo de São Vítor", "Palavra de Deus"],
    },
    "a-substancia-do-amor.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Amor Divino", "Escola Vitorina", "Hugo de São Vítor", "Mística Medieval"],
    },
    "anotacoes-sobre-salmos-118.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Escola Vitorina", "Exegese Medieval", "Hugo de São Vítor", "Salmos"],
    },
    "genealogia-espiritual-de-hugo-e-sao-tomas.md": {
        "categories": ["História", "Teologia"],
        "add_keywords": ["Escolástica", "Escola Vitorina", "História da Igreja", "Hugo de São Vítor", "Tomás de Aquino"],
    },
    "cartas.md": {
        "categories": ["História", "Teologia"],
        "add_keywords": ["Cristianismo Primitivo", "Eclesiologia", "Inácio de Antioquia", "Martírio", "Patrística"],
    },
    "comentario-sobre-a-religiao-crista.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Petrus Ramus", "Reforma Protestante", "Religião Cristã", "Teologia Sistemática"],
    },
    "petrus-ramus-e-a-reforma-educacional-do-seculo-xvi.md": {
        "categories": ["Educação", "História"],
        "add_keywords": ["História da Educação", "Humanismo", "Pedagogia", "Petrus Ramus", "Renascimento"],
    },
    "apologia-de-socrates.md": {
        "categories": ["Filosofia"],
        "add_keywords": ["Apologia", "Clássicos", "Filosofia Antiga", "Platão", "Sócrates"],
    },
    "isagoge.md": {
        "categories": ["Filosofia"],
        "add_keywords": ["Categorias Aristotélicas", "Clássicos", "Isagoge", "Lógica", "Organon", "Porfírio"],
    },
    "primeiro-livro-de-moises-chamado-genesis.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Antigo Testamento", "Bíblia", "Gênesis", "Pentateuco", "Torá"],
    },
    "segundo-livro-de-moises-chamado-exodo.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Antigo Testamento", "Bíblia", "Êxodo", "Pentateuco", "Torá"],
    },
    "a-imitacao-de-cristo-livro-1.md": {
        "categories": ["Teologia"],
        "add_keywords": ["Devotio Moderna", "Espiritualidade Cristã", "Mística", "Tomás de Kempis"],
    },
}


def update_markdown_metadata(
    content: str,
    new_categories: List[str],
    add_keywords: Optional[List[str]] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> str:
    """Atualiza de forma estruturada as chaves categories e keywords no frontmatter YAML."""
    lines = content.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        raise ValueError("O arquivo não possui delimitador inicial de frontmatter ('---').")

    fm_end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_end_idx = i
            break
    if fm_end_idx == -1:
        raise ValueError("O arquivo não possui delimitador final de frontmatter ('---').")

    fm_lines = lines[1:fm_end_idx]
    body_lines = lines[fm_end_idx + 1 :]

    cat_start = -1
    cat_end = -1
    kw_start = -1
    kw_end = -1
    existing_keywords: List[str] = []

    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        stripped = line.strip()
        if re.match(r"^(categories|category):", stripped):
            cat_start = i
            i += 1
            while i < len(fm_lines) and (
                fm_lines[i].startswith("  ")
                or fm_lines[i].startswith(" - ")
                or fm_lines[i].startswith("\t")
                or fm_lines[i].strip() == ""
            ):
                i += 1
            cat_end = i
            continue
        elif re.match(r"^keywords:", stripped):
            kw_start = i
            i += 1
            while i < len(fm_lines) and (
                fm_lines[i].startswith("  ")
                or fm_lines[i].startswith(" - ")
                or fm_lines[i].startswith("\t")
                or fm_lines[i].strip() == ""
            ):
                l_str = fm_lines[i].strip()
                if l_str.startswith("- "):
                    val = l_str[2:].strip().strip("\"'")
                    if val:
                        existing_keywords.append(val)
                i += 1
            kw_end = i
            continue
        i += 1

    all_keywords = sorted(list(set(existing_keywords + (add_keywords or []))))
    new_cat_lines = ["categories:\n"] + [f"  - {c}\n" for c in sorted(new_categories)]
    new_kw_lines = ["keywords:\n"] + [f"  - {k}\n" for k in all_keywords] if all_keywords else []

    result_fm: List[str] = []
    i = 0
    while i < len(fm_lines):
        if i == cat_start:
            result_fm.extend(new_cat_lines)
            i = cat_end
        elif i == kw_start:
            result_fm.extend(new_kw_lines)
            i = kw_end
        else:
            result_fm.append(fm_lines[i])
            i += 1

    if cat_start == -1:
        result_fm.extend(new_cat_lines)

    if kw_start == -1 and new_kw_lines:
        c_idx = -1
        for j, line in enumerate(result_fm):
            if line.startswith("categories:"):
                k = j + 1
                while k < len(result_fm) and result_fm[k].startswith("  - "):
                    k += 1
                c_idx = k
                break
        if c_idx != -1:
            result_fm = result_fm[:c_idx] + new_kw_lines + result_fm[c_idx:]
        else:
            result_fm.extend(new_kw_lines)

    if extra_fields:
        for k, v in extra_fields.items():
            if not any(re.match(rf"^{k}:", line.strip()) for line in result_fm):
                val_str = f'"{v}"' if isinstance(v, str) else str(v)
                c_idx = -1
                for j, line in enumerate(result_fm):
                    if line.startswith("categories:"):
                        c_idx = j
                        break
                if c_idx != -1:
                    result_fm.insert(c_idx, f"{k}: {val_str}\n")
                else:
                    result_fm.append(f"{k}: {val_str}\n")

    return "---\n" + "".join(result_fm).rstrip() + "\n---\n" + "".join(body_lines)


def migrate_all():
    print("🚀 Iniciando migração de metadados de artigos e e-books...\n")

    # 1. Artigos
    articles_dir = BASE_DIR / "content" / "articles"
    for art_path in articles_dir.glob("**/*.md"):
        filename = art_path.name
        if filename not in ARTICLES_MAP:
            print(f"⚠️ Artigo não mapeado: {art_path.relative_to(BASE_DIR)}")
            continue

        info = ARTICLES_MAP[filename]
        content = art_path.read_text(encoding="utf-8")
        updated = update_markdown_metadata(
            content,
            new_categories=info["categories"],
            add_keywords=info.get("add_keywords"),
            extra_fields=info.get("extra"),
        )
        art_path.write_text(updated, encoding="utf-8")
        print(f"✅ Artigo atualizado: {art_path.relative_to(BASE_DIR)} -> {info['categories']}")

    print("\n" + "-" * 50 + "\n")

    # 2. E-books
    books_dir = BASE_DIR / "content" / "books"
    for book_path in books_dir.glob("**/*.md"):
        filename = book_path.name
        if filename not in BOOKS_MAP:
            print(f"⚠️ Livro não mapeado: {book_path.relative_to(BASE_DIR)}")
            continue

        info = BOOKS_MAP[filename]
        content = book_path.read_text(encoding="utf-8")
        updated = update_markdown_metadata(
            content,
            new_categories=info["categories"],
            add_keywords=info.get("add_keywords"),
            extra_fields=info.get("extra"),
        )
        book_path.write_text(updated, encoding="utf-8")
        print(f"✅ E-book atualizado: {book_path.relative_to(BASE_DIR)} -> {info['categories']}")

    print("\n🏁 Migração concluída com sucesso!")


if __name__ == "__main__":
    migrate_all()
