# Arquitetura e Funcionamento do Projeto

O **OpenSciMD** é um repositório e plataforma CLI em **Python 3.11+ (gerenciada via `uv`)** concebida para ingestão, curadoria editorial, validação determinística, indexação imutável e compilação multiformato (Markdown, JSON API, EPUB 3, PDF/Typst para impressão KDP e banco SQLite FTS5 RAG) de artigos científicos e livros clássicos consumidos pelo leitor **LeiaME**.

---

## 🏗️ Estrutura do Repositório

```text
openscimd/
├── AGENTS.md                        # Contrato operacional e roteador para agentes de IA
├── main.py                          # Hub CLI Typer (`uv run openscimd ...`)
├── pyproject.toml                   # Dependências uv, regras ruff e mypy
├── salopdoc.yml                     # Configuração de extração/reflow do SalopDoc
├── index-articles.json              # Catálogo JSON compilado de artigos
├── index-books.json                 # Catálogo JSON compilado de livros/e-books
├── index-journals.json              # Catálogo JSON compilado de periódicos e volumes
├── .agents/                         # Playbooks modulares (pipeline, spec editorial, revisão)
├── content/                         # FONTE ÚNICA DA VERDADE publicada
│   ├── articles/<revista>/vol-<N>/  # Artigos acadêmicos aprovados (.md)
│   └── books/<autor>/               # Livros e tratados aprovados (.md)
├── data/
│   ├── raw/                         # Matrizes brutas imutáveis (PDF, HTML, MD original)
│   ├── draft/                       # Rascunhos imutáveis de extração automática
│   ├── review/                      # Mesa exclusiva de edição ativa (+ *.audit.md)
│   ├── catalog-registry.json        # Ledger append-only de IDs imutáveis (`art_XXX`/`book_XXX`)
│   └── openscimd_rag.sqlite         # Banco vetorial/textual SQLite FTS5 (BM25)
├── assets/
│   ├── covers/                      # Capas canônicas 2:3 em WebP q100 (variantes thumb/mobile/tablet/desktop via API)
│   ├── images/figures/              # Figuras internas originais (redimensionamento WebP via pipeline da API)
│   └── sources/                     # Fontes primárias públicas (PDF ou Hub HTML)
├── scripts/                         # Módulos Python da CLI e regras de negócio
│   ├── workflow.py                  # Transições start-review e promote
│   ├── validator.py                 # Validador de metadados YAML e gate individual/global
│   ├── editorial_linter.py          # Linter editorial determinístico + comparador de matriz
│   ├── indexer.py                   # Compilador de index-*.json e validação de ledger
│   ├── identity_registry.py         # Ledger imutável de IDs com checagem SQLite
│   ├── enricher.py                  # Enriquecimento via APIs Crossref e Zenodo
│   ├── text_tools.py                # Normalização de referências bíblicas com masking
│   ├── html_cleaner.py / html2md.py # Conversores HTML -> Markdown
│   ├── book_assembler.py            # Montagem modular de tratados multi-partes
│   ├── salopdoc_adapter.py          # Integração com SalopDoc (PDF -> MD)
│   ├── spellchecker/                # Revisor de arcaísmos + Hunspell pt_BR
│   ├── covers.py                    # Composição tipográfica e build WebP de capas 2:3
│   ├── md2epub.py / kindle_validator.py  # Compilador EPUB 3 e validador KDP
│   ├── md2print.py / md2pdf.py      # Compilação Typst (impresso 14x21) e PDF editorial
│   └── rag.py                       # Indexação e busca FTS5 BM25
├── tests/                           # Suíte pytest cobrindo CLI, gates, conversores e exports
└── docs/                            # Documentação técnica e editorial de referência
```

---

## ⚙️ Fluxo de Estados e Automação

```mermaid
flowchart LR
    RAW["data/raw/<br/>(Matriz Bruta Imutável)"] -->|import-pdf / saloppdf / clean-html| DRAFT["data/draft/<br/>(Rascunho Imutável)"]
    DRAFT -->|start-review| REVIEW["data/review/<br/>(Edição Ativa + .audit.md)"]
    CONTENT["content/<br/>(Acervo Publicado)"] -->|start-review<br/>(re-revisão)| REVIEW
    REVIEW -->|enrich / normalize-refs / review --check| REVIEW
    REVIEW -->|validate --file + lint| GATE{"Gate = 0 erros?"}
    GATE -->|Não| REVIEW
    GATE -->|Sim + promote| CONTENT
    CONTENT -->|index + validate-ids| INDEX["index-*.json +<br/>catalog-registry.json"]
```

### 1. Ledger Imutável de Identidades (`data/catalog-registry.json`)
Para garantir que IDs (`art_001`, `book_001`) consumidos pelo leitor **LeiaME** jamais sejam reciclados ou sequestrados ao mover ou renomear arquivos:
- O [`identity_registry.py`](../scripts/identity_registry.py) reconcilia documentos por caminho atual, `past_rel_paths`, `git diff --find-renames`, DOI, hash SHA-256 do corpo e similaridade título/autor.
- Invariantes append-only e unicidade são validadas em memória via SQLite e pelo comando `uv run openscimd validate-ids --base-ref HEAD`.

### 2. Linter Editorial e Gate Determinístico
- [`editorial_linter.py`](../scripts/editorial_linter.py) mascara frontmatter YAML, blocos de código, matemática e URLs antes de inspecionar: hierarquia de cabeçalhos e Title Case (`ED001`–`ED004`), aspas (`ED005`), integridade/sequência/ABNT de notas de rodapé (`ED006`–`ED012`), meia-risca em intervalos numéricos (`ED013`), referências bíblicas (`ED014`), artefatos de OCR (`ED015`) e desvios quantitativos contra a matriz local (`SRC001`–`SRC002`).
- [`validator.py`](../scripts/validator.py) unifica a verificação de metadados YAML com o linter no comando `uv run openscimd validate --file ...` e bloqueia promoções inválidas em `promote`.

### 3. Exportação, Capas, Figuras e RAG
- **Capas**: arte de fundo 2:3 gerada por subagente multimodal; `compose-cover` (`inject-text`) aplica a tipografia canônica e salva a matriz única em `assets/covers/<slug>.webp` (`1696×2528 px`, WebP qualidade 100). Durante o build da `leia-me/api`, o pipeline com `sharp` gera as variantes WebP q100 (`thumb` 360px, `mobile` 640px, `tablet` 1080px, `desktop` 1696px) servidas via `?size=`. Extensões auxiliares de manipulação local (`.png`, `.jpg`) podem coexistir em `assets/covers/` e são ignoradas pelo `.gitignore`.
- **Figuras internas**: o repositório mantém apenas os arquivos originais em `assets/images/figures/<arquivo>.<ext>`, referenciados diretamente nos arquivos Markdown. Durante o build da `leia-me/api`, o pipeline com `sharp` gera as variantes WebP responsivas (`mobile` 480px, `tablet` 768px, `desktop` 1200px) servidas via `?size=mobile|tablet|desktop`.
- **EPUB & Impresso**: `build-epub` + `validate-kindle` geram e auditam EPUB 3 para KDP; `build-print` compila miolo e capa aberta via Typst (`scripts/templates/book_print.typ`).
- **RAG Local**: `build-rag` e `search-rag` indexam seções semânticas em `data/openscimd_rag.sqlite` com `unicode61 remove_diacritics 2` e ranqueamento BM25.
