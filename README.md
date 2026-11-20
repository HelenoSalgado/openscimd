# 🎓 OpenSciMD — Open-Access Scientific Articles & Books in Markdown

Bem-vindo ao **OpenSciMD**, um repositório e ecossistema CLI concebido para ingestão, curadoria filológica, validação editorial determinística e distribuição multiformato (Markdown, JSON API, EPUB 3, PDF/Typst e SQLite FTS5 RAG) de artigos científicos e livros clássicos consumidos pelo leitor **LeiaME**.

---

## 🚀 Principais Recursos

- **CLI Unificado (`uv run openscimd`)**: Pipeline de ponta a ponta organizado por estágios (Ingestão → Revisão → Gates → Publicação → Capas → Exportação/RAG).
- **Linter Editorial & Auditoria contra Matriz (`lint` / `validate --file`)**: Verifica automaticamente YAML, hierarquia Title Case, aspas, meia-risca (`–`), referências bíblicas, padrão ABNT de notas e integridade quantitativa contra o original.
- **Fluxo Seguro de Revisão (`start-review` / `promote`)**: Mantém `data/raw/` e `data/draft/` imutáveis, exige mesa de revisão ativa em `data/review/` com manifesto linha a linha `.audit.md` e só promove para `content/` após aprovação nos gates.
- **Ledger Imutável de IDs (`validate-ids`)**: Garante estabilidade perpétua de `art_XXX` e `book_XXX` em `data/catalog-registry.json`.
- **Enriquecimento Bibliográfico (`enrich`)**: Consulta APIs oficiais do Crossref e Zenodo via DOI.
- **Compilação & Validação Multiformato**: EPUB 3 (`build-epub` + `validate-kindle`), livro impresso 14×21 cm via Typst (`build-print`), PDF editorial (`export-pdf`) e capas 2:3 responsivas (`ai-cover`, `inject-text`, `build-covers`).
- **Motor RAG Local (`build-rag` / `search-rag`)**: Busca textual BM25 em SQLite FTS5 pronta para pesquisa offline e LLMs.

---

## 📂 Estrutura do Repositório

- `AGENTS.md` e `.agents/`: Contrato operacional e playbooks modulares para agentes de IA.
- `content/articles/` e `content/books/`: Fonte única da verdade publicada.
- `data/raw/`: Matrizes originais brutas (PDF, HTML, MD) — **imutável**.
- `data/draft/`: Extrações automáticas iniciais — **imutável**.
- `data/review/`: Mesa de revisão ativa (+ manifestos `.audit.md`).
- `assets/covers/`, `assets/images/`, `assets/sources/`: Capas responsivas, ilustrações e documentos originais.
- `scripts/` e `tests/`: Automação Python e suíte de testes (`pytest`, `ruff`, `mypy`).
- `docs/`: Documentação arquitetural e editorial.

---

## 🛠️ Execução Rápida

O gerenciamento de dependências e execução usa exclusivamente **`uv`**:

```bash
# Instalar dependências (incluindo ferramentas dev: pytest, ruff, mypy)
uv sync

# Ver todos os comandos agrupados por fase do pipeline
uv run openscimd --help
```

### Ciclo Padrão de Trabalho

```bash
# 1. Ingestão (SalopDoc para PDF digital, ou saloppdf/clean-html conforme a fonte)
uv run openscimd import-pdf "data/raw/artigo.pdf" -o "data/draft/artigo.md"

# 2. Abrir revisão ativa (a partir de rascunho OU obra publicada em re-revisão)
uv run openscimd start-review "data/draft/artigo.md" --type articles --dest "revista/vol-1/slug.md"

# 3. Apoio à edição
uv run openscimd enrich "data/review/articles/revista/vol-1/slug.md"
uv run openscimd normalize-refs "data/review/articles/revista/vol-1/slug.md" --canonical
uv run openscimd review --check "data/review/articles/revista/vol-1/slug.md"

# 4. Gate obrigatório (YAML + Linter Editorial + Comparação com matriz)
uv run openscimd validate --file "data/review/articles/revista/vol-1/slug.md" --source "data/raw/artigo.pdf"

# 5. Promover para content/ e atualizar índices (somente após aprovação)
uv run openscimd promote "data/review/articles/revista/vol-1/slug.md" --source "data/raw/artigo.pdf" --index
```

### Exportação, Capas, RAG e Qualidade de Código

```bash
# Gerar e validar EPUB 3 / Impresso / PDF / RAG
uv run openscimd build-epub "content/books/platao/fedon.md"
uv run openscimd validate-kindle "dist/content/books/platao/fedon.epub"
uv run openscimd build-print "content/books/platao/fedon.md"
uv run openscimd build-rag && uv run openscimd search-rag "Sócrates justiça" --ai

# Capas (ver Design Systems em .agents/editorial/)
uv run openscimd ai-cover <slug> --provider gemini
uv run openscimd build-covers

# Testes e rigor estático
uv run ruff check .
uv run mypy scripts/editorial_linter.py scripts/workflow.py scripts/validator.py scripts/categories.py scripts/enricher.py scripts/text_tools.py scripts/biblical_books.py scripts/html_cleaner.py scripts/book_assembler.py scripts/utils.py scripts/identity_registry.py
uv run pytest
uv run openscimd validate
uv run openscimd validate-ids --base-ref HEAD
```

---

## 🤝 Como Contribuir

- **Revisões Textuais:** Consulte o **[Guia de Contribuição](CONTRIBUTING.md)** e abra uma **[Issue de Revisão Textual](https://github.com/helenosalgado/openscimd/issues/new?template=revisao_textual.yml)**.
- **Documentação Detalhada:**
  1. [Arquitetura do Repositório](docs/arquitetura.md)
  2. [Fluxo de Trabalho em 5 Estágios](docs/fluxo-de-trabalho.md)
  3. [Diretrizes de Metadados (MDC)](docs/metadata_guidelines.md)
  4. [Padrão de Notas e Aparato Crítico](docs/padrao-de-notas-e-aparato-critico.md)
  5. [Design System de Capas — Artigos](.agents/editorial/design-system-capas-artigos.md) e [Livros](.agents/editorial/design-system-capas-livros.md)

---

## 📖 Como Citar o OpenSciMD

### BibTeX
```bibtex
@dataset{salgado2026openscimd,
  author       = {Heleno Salgado},
  title        = {{OpenSciMD}: Open-Access Scientific Articles in Markdown},
  year         = {2026},
  publisher    = {GitHub},
  version      = {1.0.0},
  url          = {https://github.com/HelenoSalgado/openscimd},
  note         = {Corpus acadêmico curado e estruturado em Markdown com enriquecimento de metadados}
}
```

### ABNT
```text
SALGADO, Heleno. OpenSciMD: Open-Access Scientific Articles in Markdown. Versão 1.0.0. 2026. Disponível em: https://github.com/HelenoSalgado/openscimd.
```

---

## ⚖️ Licença e Direitos Autorais

- **Compilação, Metadados, Capas e Código:** **[CC BY-NC-ND 4.0](LICENSES.md)**.
- **Conteúdo Individual das Obras:** permanece sob a licença original declarada no YAML de cada documento (ex.: CC BY 4.0, CC BY-NC 4.0, Domínio Público).
