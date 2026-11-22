# Fluxo de Trabalho e Contribuição

Este guia detalha o fluxo completo de cinco estágios para adicionar, revisar, validar e publicar artigos científicos e livros no **OpenSciMD**.

> [!NOTE]
> Para a especificação editorial detalhada (tipografia, ABNT, namespaces de notas e regras para IA), consulte [`AGENTS.md`](../AGENTS.md) e [`.agents/01-editorial-spec.md`](../.agents/01-editorial-spec.md).

---

## 🔄 Os 5 Estágios do Pipeline

1. **Ingestão (`data/raw/` → `data/draft/`)**: converta PDF ou HTML bruto para rascunho Markdown sem editar os arquivos originais.
2. **Preparo (`data/draft/` ou `content/` → `data/review/`)**: abra uma mesa de revisão ativa com `start-review`.
3. **Edição & Auditoria (`data/review/`)**: enriqueça metadados, normalize referências bíblicas, verifique ortografia e faça a leitura integral bloco a bloco registrando no `.audit.md`.
4. **Gate (`validate --file` / `lint`)**: confirme **0 erros** de metadados, linter editorial e comparação contra a matriz.
5. **Publicação (`promote` → `content/`)**: mova o documento validado para `content/` (removendo a cópia ativa de `data/review/`), atualize os índices e verifique o ledger de IDs.

---

## 📥 Passo 1 — Ingestão a partir de PDF ou HTML

Deposite o arquivo original na pasta `data/raw/` (estritamente imutável).

- **PDF digital com texto selecionável (SalopDoc)**:
  ```bash
  uv run openscimd import-pdf "data/raw/nome-do-artigo.pdf" -o "data/draft/nome-do-artigo.md"
  # Ou em lote:
  uv run openscimd batch-import
  ```
- **PDF escaneado, multi-coluna complexo ou com muitas tabelas/notas**:
  Use `saloppdf` (MinerU) conforme [`docs/saloppdf.md`](saloppdf.md).
- **HTML legado com tabelas de layout**:
  ```bash
  uv run openscimd clean-html "data/raw/obra.htm" "data/draft/obra.md" --author "Nome do Autor"
  ```
- **HTML moderno / frames**:
  ```bash
  uv run openscimd html-to-md "data/raw/obra.html" "data/draft/obra.md"
  ```

---

## ✍️ Passo 2 e 3 — Abrir Revisão Ativa e Editar (`data/review/`)

Nunca edite em `data/draft/` nem edite diretamente em `content/`. Inicie sempre via `start-review`:

```bash
# Para nova obra vinda de data/draft/:
uv run openscimd start-review "data/draft/nome-do-artigo.md" --type articles --dest "revista/vol-1/slug.md"
# ou para livro:
uv run openscimd start-review "data/draft/obra.md" --type books --dest "autor/slug.md"

# Para re-revisar uma obra já publicada em content/:
uv run openscimd start-review "content/articles/revista/vol-1/slug.md"
```

Durante a edição em `data/review/`:
1. **Enriquecer metadados via DOI (Crossref ou Zenodo)**:
   ```bash
   uv run openscimd enrich "data/review/articles/revista/vol-1/slug.md"
   ```
2. **Normalizar referências bíblicas**:
   ```bash
   uv run openscimd normalize-refs "data/review/.../slug.md" --canonical
   ```
3. **Checagem ortográfica e de arcaísmos**:
   ```bash
   uv run openscimd review --check "data/review/.../slug.md"
   ```
4. **Conferência linha a linha**: leia em blocos de 150–200 linhas contra a fonte em `data/raw/` e marque os blocos concluídos no arquivo irmão `<slug>.audit.md` (ver [`.agents/03-line-by-line-review.md`](../.agents/03-line-by-line-review.md)).

### Modelo de Frontmatter YAML (Artigos)

```yaml
---
title: "Reformas Filosóficas de Petrus Ramus: A Simplificação da Lógica"
journal: "History of Science"
volume: 6
issue: 5
pages: "101–112"
e_issn: "2790-0037"

authors:
  - name: "Nome do Autor 1"
    orcid: "0000-0000-0000-0000"
    email: "email@example.com"
    affiliation: "Universidade Estatal de Baku"

summary: "Resumo acadêmico integral do artigo original."
date: "2026-06-20"
language: "pt-BR"
originalLanguage: "en"
license: "CC BY 4.0"

UDC: "1:94"
BBK: "87.3:87.4"
HoS: "113"
DOI: "10.33864/2790-0037.2025.v6.i5.101-112"

keywords:
  - Renascimento
  - Humanismo
  - Petrus Ramus

categories:
  - Filosofia
  - História
---
```

> [!NOTE]
> Use `authors` (lista estruturada) para artigos e `author` (ou `authors`) para livros. Livros **não** podem ter `keywords`. Veja todas as regras em [`docs/metadata_guidelines.md`](metadata_guidelines.md).

---

## 🛡️ Passo 4 — Gate de Validação Obrigatório

Antes de promover qualquer obra:

```bash
uv run openscimd validate --file "data/review/.../slug.md" --source "data/raw/original.pdf"
# Para validar também warnings em modo estrito:
uv run openscimd lint "data/review/.../slug.md" --source "data/raw/original.pdf" --strict
```

---

## 🚀 Passo 5 — Capas, Fontes, Promoção e Indexação

1. **Fonte Original (`assets/sources/`)**: salve o arquivo original como `assets/sources/<slug>.pdf` (ou `<slug>.html` para hubs de múltiplas fontes, conforme [`docs/readers/leiame.md`](readers/leiame.md)).
2. **Imagem de Capa (`assets/covers/`)**: gere a arte de fundo 2:3 sem texto via subagente multimodal (`image-generator`) seguindo os Design Systems e componha a tipografia editorial canônica diretamente em `assets/covers/<slug>.webp` (WebP q100):
   - Artigos: [`.agents/editorial/design-system-capas-artigos.md`](../.agents/editorial/design-system-capas-artigos.md)
   - Livros: [`.agents/editorial/design-system-capas-livros.md`](../.agents/editorial/design-system-capas-livros.md)
   ```bash
   uv run openscimd compose-cover <caminho-da-arte> --slug <slug>
   # Ou pelo alias equivalente:
   uv run openscimd inject-text <caminho-da-arte> --slug <slug>
   ```
3. **Promover e Indexar**:
   ```bash
   uv run openscimd promote "data/review/.../slug.md" --source "data/raw/original.pdf" --index
   ```
   O comando valida novamente, move o arquivo para `content/`, remove a cópia e o `.audit.md` de `data/review/`, atualiza `index-*.json` e checa `validate-ids`.

---

## 🧪 Como Executar Validações e Testes

```bash
# Validação global de metadados do acervo publicado
uv run openscimd validate

# Validação global incluindo linter editorial
uv run openscimd validate --editorial

# Verificação de invariantes do ledger de IDs
uv run openscimd validate-ids --base-ref HEAD

# Suíte de testes unitários e de integração
uv run pytest

# Linter de código e checagem estática de tipos
uv run ruff check .
uv run mypy scripts/editorial_linter.py scripts/workflow.py scripts/validator.py scripts/categories.py scripts/enricher.py scripts/text_tools.py scripts/biblical_books.py scripts/html_cleaner.py scripts/book_assembler.py scripts/utils.py scripts/identity_registry.py
```
