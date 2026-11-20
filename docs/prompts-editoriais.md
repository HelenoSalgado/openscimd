# Catálogo de Prompts Editoriais Recomendados para IA

Este documento reúne os **modelos de prompts oficiais e recomendados** para trabalhar com Agentes de IA no ecossistema OpenSciMD, alinhados ao contrato operacional em [`AGENTS.md`](../AGENTS.md) e aos playbooks modulares em `.agents/`.

---

## 🧭 Regras Gerais para Todos os Comandos de IA

1. **Fonte Única da Verdade**: Consulte [`AGENTS.md`](../AGENTS.md) e os playbooks `.agents/00-pipeline.md`, `.agents/01-editorial-spec.md`, `.agents/02-translation-protocol.md` e `.agents/03-line-by-line-review.md`.
2. **Imutabilidade de `data/raw/` e `data/draft/`**: Inicie sempre via `uv run openscimd start-review ...` e opere exclusivamente em `data/review/`.
3. **Incorrupção da Prosa**: Nunca reescreva, parafraseie, resuma ou modernize vocabulário de traduções humanas fornecidas.
4. **Leitura Integral em Blocos + Gate**: Proibido declarar revisão concluída sem preencher 100% do manifesto `<obra>.audit.md` (blocos de 150–200 linhas) e passar com 0 erros em `uv run openscimd validate --file ...`.

---

## 📋 Contextos Operacionais e Modelos de Prompts

### Contexto 1: Saneamento e Formatação de Tradução / Rascunho sem Matriz Original

> **Cenário:** Você tem um rascunho de tradução humana em `data/draft/<arquivo>.md` (sem a matriz original no repositório) e deseja iniciá-lo e saneá-lo em `data/review/`.

```text
Siga integralmente @[AGENTS.md], @[.agents/00-pipeline.md], @[.agents/01-editorial-spec.md] e @[.agents/03-line-by-line-review.md].

1. Inicie a revisão via `uv run openscimd start-review data/draft/<nome-do-arquivo>.md --type books --dest <autor>/<slug>.md`.
2. Mantenha data/draft/ 100% intacto; edite exclusivamente em data/review/books/<autor>/<slug>.md.
3. INCORRUPÇÃO DA PROSA: Não altere, reescreva, resuma ou parafraseie nenhuma palavra da tradução de <Nome do Tradutor>; preserve glosas entre colchetes [...].
4. FRONTMATTER YAML: Preencha title (Title Case), author, summary, translator, originalLanguage (<la|el|en|he>), language ("pt-BR" ou "pt-PT"), date e categories (sem keywords, pois é livro). Metadados não vão no corpo.
5. CABEÇALHOS E TIPOGRAFIA: Sem H1 (#) no corpo; cabeçalhos em Title Case (exceto algarismos romanos); nunca use **negrito** em títulos (*itálico* permitido); use aspas curvas (“” / ‘’ — ou «» se clássico) e meia-risca (–) em intervalos numéricos.
6. NOTAS E PAGINAÇÃO CRÍTICA: Padronize paginação [N] para (Página. Linha). Use padrão ABNT para âncoras (palavra[^1].) e namespaces [^ne1]/[^ne2] (Editoriais), [^nt1] (Tradutor), [^1] (Autor), após um único `---` e subseções `###`.
7. AUDITORIA E GATE: Leia o texto integral em blocos de 150–200 linhas registrando cada bloco em .audit.md e rode `uv run openscimd normalize-refs ...`, `uv run openscimd review --check ...` e `uv run openscimd validate --file ...` até obter 0 erros.
```

---

### Contexto 2: Tradução e/ou Auditoria Filológica com Matriz em `data/raw/` (1:1 Offline)

> **Cenário:** O texto original está em `data/raw/<original>` e a tradução em `data/draft/<arquivo>.md`.

```text
Siga @[AGENTS.md], @[.agents/01-editorial-spec.md], @[.agents/02-translation-protocol.md] e @[.agents/03-line-by-line-review.md].

Audite e revise data/draft/<arquivo>.md confrontando 100% em modo OFFLINE contra @data/raw/<original>, operando na cópia criada por `uv run openscimd start-review`.

Diretrizes obrigatórias:
1. CONTENÇÃO OFFLINE: Proibido usar busca web ou memória paramétrica para reconstituir trechos do corpo textual.
2. CORRESPONDÊNCIA 1:1: Leia em blocos de 150–200 linhas preenchendo o arquivo .audit.md; confira seções, diálogos (Interlocutor — ), notas e parágrafos sem omissões ou resumos silenciosos.
3. ZERO PARÁFRASE: Corrija suavizações de LLM restaurando a literalidade e consistência terminológica do original.
4. PADRÕES EDITORIAIS: Âncoras ABNT (palavra[^1].), referências bíblicas canônicas (Jo 3.16), meia-risca (–) em intervalos, itálico em termos estrangeiros e YAML com language ("pt-BR" ou "pt-PT") e originalLanguage.
5. GATE FINAL: Execute `uv run openscimd review --check` e `uv run openscimd validate --file <review_md> --source data/raw/<original> --translated` até zerar os erros.
```

---

### Contexto 3: Conversão e Curadoria de Artigo Acadêmico (PDF + Crossref/Zenodo)

> **Cenário:** Artigo extraído via `openscimd import-pdf` ou `saloppdf` para `data/draft/<artigo>.md`.

```text
Siga @[AGENTS.md], @[.agents/00-pipeline.md], @[.agents/01-editorial-spec.md] e @[.agents/03-line-by-line-review.md].

1. Execute `uv run openscimd start-review data/draft/<artigo>.md --type articles --dest <revista>/vol-<N>/<slug>.md`.
2. Rode `uv run openscimd enrich <review_md>` para consultar Crossref/Zenodo e complete manualmente via registro oficial qualquer campo faltante (authors com orcid/email/affiliation, journal, volume igual a vol-<N>, issue, pages com meia-risca, date ISO YYYY-MM-DD ou ABNT, language "pt-BR"/"pt-PT", DOI, categories e keywords).
3. Transcreva o resumo original 100% integral no campo `summary` do YAML e remova-o do corpo.
4. Remova ruídos de OCR, cabeçalhos repetidos de página e recomponha parágrafos partidos em viradas de página.
5. Rebaixe notas presas ao título/autor para o primeiro cabeçalho do corpo (ex.: `## Introdução[^1][^ne1]`), mantendo notas do autor integrais (`[^1]`..`[^N]`), âncoras no padrão ABNT (`palavra[^1].`) e único `---` com `### Notas...` no final.
6. Preencha 100% do `.audit.md` lendo bloco a bloco contra @data/raw/<artigo>.pdf e valide com `uv run openscimd validate --file <review_md> --source data/raw/<artigo>.pdf`.
```

---

### Contexto 4: Re-revisão de Obra Já Publicada (`content/`)

> **Cenário:** Correção ou saneamento editorial de obra já publicada em `content/articles/` ou `content/books/`.

```text
Siga @[AGENTS.md], @[.agents/01-editorial-spec.md] e @[.agents/03-line-by-line-review.md].

1. Copie a obra para edição ativa com `uv run openscimd start-review content/<subcaminho>/<obra>.md`.
2. Audite integralmente em blocos de 150–200 linhas registrando em `.audit.md`, aplicando: Title Case nos cabeçalhos (exceto algarismos romanos), remoção de H1/negrito em cabeçalhos, aspas curvas (“” / ‘’ ou «»), meia-risca (–) em intervalos numéricos, padrão ABNT em notas (`palavra[^1].`), namespaces `[^ne]`/`[^nt]`/`[^1]` e `language` (`pt-BR`/`pt-PT`).
3. Valide com `uv run openscimd validate --file data/review/<subcaminho>/<obra>.md --strict`.
4. Somente após minha aprovação explícita, promova de volta com `uv run openscimd promote data/review/<subcaminho>/<obra>.md --index`.
```

---

## 🛠️ Comandos CLI de Apoio Editorial

| Ação | Comando |
| :--- | :--- |
| **Iniciar revisão ativa** | `uv run openscimd start-review <origem> [--type articles\|books --dest <subcaminho>]` |
| **Enriquecer YAML via DOI** | `uv run openscimd enrich "data/review/.../arquivo.md"` |
| **Normalizar referências bíblicas** | `uv run openscimd normalize-refs "data/review/.../arquivo.md"` |
| **Checagem ortográfica / arcaísmos** | `uv run openscimd review --check "data/review/.../arquivo.md"` |
| **Linter editorial (isolado ou lote)** | `uv run openscimd lint "data/review/.../arquivo.md" [--source <orig>] --strict` |
| **Gate completo (YAML + Linter + Fonte)** | `uv run openscimd validate --file "data/review/.../arquivo.md" [--source <orig>]` |
| **Promover para `content/` + indexar** | `uv run openscimd promote "data/review/.../arquivo.md" [--source <orig>] --index` |
