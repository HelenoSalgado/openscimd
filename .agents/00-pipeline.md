# 00 — Pipeline Operacional do OpenSciMD

Este documento define o fluxo de estados de qualquer obra no repositório e a seleção determinística de ferramentas.

---

## 1. Máquina de Estados dos Diretórios

```text
1. MATRIZ BRUTA      data/raw/         (IMUTÁVEL — PDF, HTML, MD original no idioma-fonte)
                         │
                         ▼  [import-pdf | saloppdf | clean-html | html-to-md]
2. RASCUNHO          data/draft/       (IMUTÁVEL — saída bruta de extração/conversão)
                         │
                         ▼  [uv run openscimd start-review <origem> ...]
3. EDIÇÃO ATIVA      data/review/      (ÚNICA pasta editável + arquivo <obra>.audit.md)
                         ▲
                         │  [uv run openscimd start-review content/<...>.md] (re-revisão)
                         │
                         ▼  [uv run openscimd validate --file ... --source ...] (GATE = 0 erros)
                         ▼  [uv run openscimd promote <review_file> --index] (com aval humano)
4. PUBLICAÇÃO        content/          (Fonte única da verdade publicada; sai de data/review/)
```

### Regras de Transição
- **Nunca mova nem apague** arquivos em `data/raw/` ou `data/draft/`. `start-review` sempre faz uma **cópia**.
- **Obras já publicadas em re-revisão**: sempre que um documento em `content/` precisar de nova revisão ou saneamento, inicie com `uv run openscimd start-review content/<...>/<obra>.md`. Isso espelha a obra em `data/review/` no mesmo caminho relativo, deixando-a em edição ativa sem duplicação permanente após o término.
- **Promoção (`promote`)**: bloqueia automaticamente se `validate --file` acusar qualquer erro de metadados ou lint editorial. Quando aprovada, atualiza `content/`, remove a cópia e o `.audit.md` de `data/review/` e opcionalmente atualiza os índices (`--index`).

---

## 2. Árvore de Decisão na Ingestão

1. **PDF digital com texto selecionável e layout simples/médio**:
   ```bash
   uv run openscimd import-pdf "data/raw/arquivo.pdf" -o "data/draft/slug.md"
   ```
   Ou em lote: `uv run openscimd batch-import`.
2. **PDF escaneado, multi-coluna complexo, muitas notas ou fórmulas**:
   Use `saloppdf` (MinerU) conforme [`docs/saloppdf.md`](../docs/saloppdf.md), gerando artefatos em `artfacts-saloppdf/` e copiando o Markdown final para `data/draft/<slug>.md`.
3. **HTML legado com tabelas de layout, tags `<font>` e encoding `ISO-8859-1` / `Windows-1252`**:
   ```bash
   uv run openscimd clean-html "data/raw/obra.htm" "data/draft/obra.md" --author "Nome do Autor"
   ```
4. **HTML moderno ou com `<frame>` / `<iframe>`**:
   ```bash
   uv run openscimd html-to-md "data/raw/obra.html" "data/draft/obra.md"
   ```
5. **Livro modular compilado de múltiplas partes já revisadas**:
   ```bash
   uv run openscimd assemble-book "data/review/books/<obra-partes>" "data/review/books/<obra>.md" \
     --title "Título" --author "Autor" --date "Data" --license "Licença"
   ```

---

## 3. Sequência Obrigatória Durante a Edição (`data/review/`)

Execute nesta ordem exata:

1. **Abrir mesa de revisão**:
   ```bash
   # Novo rascunho de artigo ou livro:
   uv run openscimd start-review "data/draft/artigo.md" --type articles --dest "revista/vol-1/slug.md"
   uv run openscimd start-review "data/draft/livro.md" --type books --dest "autor/slug.md"

   # Re-revisão de obra já publicada:
   uv run openscimd start-review "content/articles/revista/vol-1/slug.md"
   ```
2. **Preencher e enriquecer YAML** (se artigo com DOI):
   ```bash
   uv run openscimd enrich "data/review/articles/revista/vol-1/slug.md"
   ```
   Confira manualmente `volume`, `issue`, `pages`, `authors` (`orcid`, `email`, `affiliation`), `summary` integral, `categories`, `keywords`, `language`, `date`.
3. **Normalizar citações bíblicas** (quando houver):
   ```bash
   uv run openscimd normalize-refs "data/review/.../slug.md" --canonical
   ```
4. **Executar revisão ortográfica/arcaísmos**:
   ```bash
   uv run openscimd review --check "data/review/.../slug.md"
   ```
   Corrija no texto apenas erros genuínos de OCR/ortografia (nunca altere escolhas lexicais intencionais de tradutor humano).
5. **Auditoria humana/IA linha a linha em blocos** (`.agents/03-line-by-line-review.md`):
   Leia e confronte todo o texto em blocos de 150–200 linhas contra a fonte original em `data/raw/` ou `data/draft/`, preenchendo o arquivo `.audit.md`.
6. **Passar no Gate determinístico**:
   ```bash
   uv run openscimd validate --file "data/review/.../slug.md" --source "data/raw/original.pdf"
   # Para validação estrita incluindo warnings:
   uv run openscimd lint "data/review/.../slug.md" --source "data/raw/original.pdf" --strict
   ```
7. **Promover (somente com aprovação do usuário)** e conferir catálogo:
   ```bash
   uv run openscimd promote "data/review/.../slug.md" --source "data/raw/original.pdf" --index
   uv run openscimd validate
   uv run openscimd validate-ids --base-ref HEAD
   ```

---

## 4. Erros Comuns Que Bloqueiam o Gate

- Deixar placeholders do `salopdoc` (`"Sem Título"`, `"Desconhecido"`, `"Geral"`).
- Divergência entre `volume` no YAML e a pasta `vol-{N}`.
- Incluir `keywords` em livro (`content/books/`).
- Usar `# ` (H1) no corpo, `**negrito**` em cabeçalho ou CAIXA ALTA em cabeçalho não-romano.
- Colocar âncora de nota após o ponto (`.[^1]`) em vez do padrão ABNT (`palavra[^1].`).
- Usar hífen `-` em intervalos numéricos (`10-15`, `Jo 1.1-14`) em vez de meia-risca (`–`).
- Deixar aspas retas `"` no corpo fora de YAML ou blocos de código.
