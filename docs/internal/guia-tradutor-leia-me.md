# Guia de Tradução, Conversão e Edição em Markdown para o OpenSciMD e LeiaME

Este guia estabelece o padrão editorial, filológico e estrutural para quem traduz ou converte artigos científicos, tratados clássicos e e-books para o ecossistema **OpenSciMD** e para o aplicativo de leitura **LeiaME**.

### Fluxo Geral de Contribuição

1. **Geração Inicial via CLI ou IA:** Extraia o PDF/HTML bruto de `data/raw/` para `data/draft/` (ex.: `uv run openscimd import-pdf`) ou utilize os [Prompts Recomendados (Apêndice)](#apêndice-prompts-recomendados-para-ia).
2. **Revisão Linha a Linha (`data/review/`):** Copie para revisão ativa via `uv run openscimd start-review`, valide a fidelidade textual bloco a bloco contra o original, remova ruídos de diagramação e confira todas as notas.
3. **Validação e Envio:** Garanta **0 erros** em `uv run openscimd validate --file ...` e envie o par de arquivos com o mesmo nome em *kebab-case*: o `.md` e a fonte original correspondente (`.pdf`).

---

## 1. Princípios Editoriais e Filológicos

- **Integralidade:** O texto-fonte é a autoridade absoluta. É terminantemente proibido resumir, condensar, expurgar ou censurar trechos, títulos ou notas.
- **Registro Formal:** Empregue português formal, culto e erudito (`pt-BR` ou `pt-PT` conforme o caso), preservando a gravidade e o tom da obra original.
- **Rigor Terminológico:** Mantenha estabilidade e homogeneidade terminológica ao longo de toda a obra e série.
- **Vocabulário Fiel:** Se um termo contemporâneo não capturar a precisão do autor histórico, prefira o correspondente vernáculo clássico ou adicione uma Nota do Tradutor (`[^nt1]`).
- **Preservação da Ambiguidade:** Onde o original for aberto ou polissêmico, preserve a mesma abertura na tradução.
- **Inviolabilidade:** Não insira glosas explicativas no fluxo dos parágrafos; use exclusivamente o namespace `[^ntN]`.

---

## 2. Padrões Estruturais e Tipográficos

- **Títulos e Cabeçalhos (*Title Case*):** O campo `title` no YAML e todos os cabeçalhos no corpo (`##`, `###`, `####`) usam **Title Case** (exceção apenas para algarismos romanos como `## VIII` ou `### Capítulo IV` e siglas técnicas). É proibido `#` (H1) no corpo e `**negrito**` em cabeçalhos; `*itálico*` é permitido.
- **Parágrafos Contínuos (*Unwrapped*):** Cada parágrafo deve ser uma linha contínua sem quebras duras artificiais no meio de frases.
- **Aspas, Intervalos e Referências Bíblicas:** Use aspas tipográficas curvas (`“...”` / `‘...’`) ou guillemets (`«...»`) para elegância clássica; nunca deixe aspas retas `"` no corpo. Use **meia-risca (`–`)** em intervalos numéricos (`101–112`, `Jo 1.1–14`). Em citações bíblicas, preserve a forma do texto (abreviado `Jo 3.16`, `Hb 11.1`, `1Co 15.3–4`; extenso `João 3.16`, `Hebreus 11.1`, `1 Coríntios 15.3–4`; ou narrativo `A Segunda Carta aos Coríntios 2.1`), corrigindo apenas variantes fora do padrão (`HB` → `Hb`, `Mat.` → `Mt`, `1Coríntios` / `I Coríntios` → `1 Coríntios`) e sempre usando ponto (`.`) entre capítulo e versículo.
- **Citações Longas:** Passagens destacadas ou com mais de três linhas vão em bloco de citação (`> `) separado por linha em branco antes e depois.
- **Ênfases e Termos Estrangeiros:** Use `*itálico*` para termos em latim, grego, hebraico e títulos de obras; use `**negrito**` para definições conceituais no corpo.
- **Notas de Rodapé (Padrão ABNT e *Namespaces*):**
  - A âncora fica **colada antes da pontuação**, sem espaço prévio (ex.: `termo[^1].`, `“citação”[^nt1].`).
  - Use `[^1]`..`[^N]` exclusivamente para Notas do Autor; `[^nt1]`.. para Notas do Tradutor; `[^ne1]`.. para Notas Editoriais.
  - Declare todas as notas ao final após um **único separador `---`**, agrupadas em subseções `###` e separadas por linha em branco:

    ```markdown
    ---

    ### Notas do Tradutor

    [^nt1]: Esclarecimento filológico sobre o termo grego.

    ### Notas do Autor

    [^1]: Conteúdo integral da nota aqui.
    ```

- **Cabeçalho de Metadados (YAML):** Todo arquivo inicia na Linha 1 com delimitadores `---`.

---

## 3. Checklist Rápido de Qualidade

- [ ] Possui o arquivo `.md` finalizado e a fonte original correspondente em *kebab-case*.
- [ ] O YAML inicia com `---` e inclui `language` (`"pt-BR"` ou `"pt-PT"`), `date` (ISO/ABNT para artigos; histórica para livros) e `categories` canônicas.
- [ ] Títulos e cabeçalhos estão em *Title Case* (exceto algarismos romanos), sem H1 nem negrito.
- [ ] Aspas curvas (`“”`) ou `«»` no corpo; meia-risca (`–`) em intervalos numéricos; referências bíblicas com ponto (`Jo 3.16`).
- [ ] Âncoras no padrão ABNT (`palavra[^1].`) e notas integrais com namespaces separados (`[^1]`, `[^nt1]`, `[^ne1]`).
- [ ] Passou com **0 erros** em `uv run openscimd validate --file <arquivo>.md`.

---

## Apêndice: Prompts Recomendados para IA

### A. Prompt para Artigos Acadêmicos e Científicos

```text
Você é um editor acadêmico do projeto OpenSciMD. Converta o texto integralmente para Markdown Puro e Semântico em português formal, sem nunca resumir nem parafrasear. Siga rigorosamente o modelo YAML e as regras abaixo:

---
title: "Reformas Filosóficas de Petrus Ramus: A Simplificação da Lógica e a Sistematização da Metodologia"
journal: "History of Science"
volume: 6
issue: 5
pages: "101–112"
e_issn: "2790-0037"
authors:
  - name: "Djamila Abdullazade"
    orcid: "0009-0007-5639-8512"
    email: "jamila.abdullazadee@gmail.com"
    affiliation: "Universidade Estatal de Baku"
summary: "Resumo integral do artigo original sem cortes."
date: "2026-06-20"
language: "pt-BR"
originalLanguage: "en"
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
license: "CC BY-NC 4.0"
---

Regras obrigatórias:
1. Title Case no `title` e em todos os cabeçalhos (`##`, `###`), nunca CAIXA ALTA (exceto algarismos romanos) nem negrito; sem H1 (`#`) no corpo.
2. Aspas curvas (“...” / ‘...’) e meia-risca (–) em intervalos numéricos (101–112). Citações longas (>3 linhas) em blocos `> `.
3. Âncoras no padrão ABNT coladas antes da pontuação (`palavra[^1].`), usando `[^1]`..`[^N]` para o autor e `[^nt1]`.. para Notas do Tradutor, declaradas no final após um único `---` sob cabeçalhos `###`.
```

### B. Prompt para E-books e Tratados Clássicos

```text
Você é um editor de e-books clássicos do projeto OpenSciMD. Converta ou traduza o texto integralmente para Markdown Puro e Semântico em português formal e erudito, sem resumir nem censurar. Use o modelo YAML abaixo (livros NÃO possuem `keywords`):

---
title: "Título da Obra em Title Case"
author: "Nome do Autor"
summary: "Sinopse fiel do conteúdo e escopo da obra."
date: "c. 1130 d.C."
license: "Domínio Público"
originalLanguage: "la"
language: "pt-BR"
translator: "Nome do Tradutor"
categories:
  - Filosofia
  - Teologia
---

Regras obrigatórias:
1. Title Case no `title` e em todos os cabeçalhos (`##`, `###`), exceto algarismos romanos; sem H1 (`#`) no corpo nem negrito em títulos.
2. Aspas curvas (“” / ‘’) ou guillemets («») para elegância clássica; meia-risca (–) em intervalos numéricos.
3. Âncoras no padrão ABNT (`palavra[^1].`), namespaces `[^ne1]` (Notas Editoriais), `[^nt1]` (Notas do Tradutor) e `[^1]` (Notas do Autor) ao final após um único `---` sob subseções `###`.
```
