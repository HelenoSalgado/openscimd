# 01 — Especificação Editorial Única (Fonte da Verdade)

Este documento consolida todas as regras de metadados YAML, estrutura Markdown, tipografia e aparato crítico do **OpenSciMD / LeiaME**. Em caso de conflito com documentos antigos, **este arquivo prevalece**.

---

## 1. Frontmatter YAML Canônico

### 1.1. Artigos Acadêmicos (`content/articles/<periodico>/vol-<N>/<slug>.md`)

```yaml
---
title: "Reformas Filosóficas de Petrus Ramus: A Simplificação da Lógica"
authors:
  - name: "Djamila Abdullazade"
    orcid: "0009-0007-5639-8512"
    email: "jamila.abdullazadee@gmail.com"
    affiliation: "Universidade Estatal de Baku"
summary: "Resumo integral do artigo original sem cortes."
date: "2026-06-20"
license: "CC BY 4.0"
journal: "History of Science"
volume: 6
issue: 5
pages: "101–112"
e_issn: "2790-0037"
DOI: "10.33864/2790-0037.2025.v6.i5.101-112"
UDC: "1:94"
BBK: "87.3:87.4"
HoS: "113"
language: "pt-BR"
originalLanguage: "en"
translator: "Nome do Tradutor"
categories:
  - Filosofia
  - História
keywords:
  - Humanismo
  - Lógica
  - Petrus Ramus
---
```

**Regras obrigatórias para Artigos:**
1. **Campos obrigatórios**: `title`, `authors` (ou `author`), `summary`, `date`, `license`, `pages`, `categories`, `language`.
2. **`language`**: use `"pt-BR"` (ou `"pt-PT"` quando aplicável). Não use `"pt"` genérico nem deixe ausente.
3. **`date`**: use ISO `"YYYY-MM-DD"` ou padrão ABNT brasileiro (`"DD-MM-YYYY"`, `"DD/MM/YYYY"`, `"20 nov. 2025"`, `"20 de novembro de 2025"`). Prefira ISO `"YYYY-MM-DD"` em novas publicações.
4. **`summary`**: transcreva o resumo original **100% integral** no YAML e remova-o do corpo do texto.
5. **`volume` e pasta `vol-{N}`**: o `volume` no YAML deve coincidir exatamente com o `{N}` da pasta `vol-{N}`.
   - **Armadilha do Crossref**: APIs frequentemente retornam `issue: "1(2)"` ou `volume: null` para o Volume 2. Nunca grave `volume: 1, issue: 2` se o artigo pertence ao `vol-2` (o correto é `volume: 2, issue: 1`).
6. **`keywords`**: uso permitido e recomendado em artigos; **proibido** em livros.

### 1.2. Livros e Tratados Clássicos (`content/books/<autor>/<slug>.md`)

```yaml
---
title: "A Imitação de Cristo: Livro I"
author: "Thomas à Kempis"
summary: "Sinopse fiel do escopo e da tese do tratado."
date: "1418 d.C."
license: "Domínio Público"
language: "pt-BR"
originalLanguage: "en"
translator: "Nome do Tradutor"
categories:
  - Teologia
---
```

**Regras obrigatórias para Livros:**
1. **Campos obrigatórios**: `title`, `author` (ou `authors`), `summary`, `date`, `license`, `categories`, `language`.
2. **`date`**: data histórica canônica quando aplicável (`"399 a.C."`, `"c. 1130 d.C."`, `"1576"`, `"1914"`).
3. **`originalLanguage`**: indica o **idioma do arquivo-fonte bruto em `data/raw/`** usado nesta edição/tradução (ex.: `"en"` se traduzido de matriz inglesa, `"la"` se direto do latim, `"el"` do grego, `"he"` do hebraico).
4. **Proibição de `keywords`**: livros **nunca** possuem a chave `keywords`.
5. **Créditos exclusivos no YAML**: autoria, `translator`, data e licença ficam somente no YAML. Não insira linhas redundantes como `_Tradução de..._` no corpo do texto.

### 1.3. Categorias Canônicas (`categories`)

- Lista **ordenada alfabeticamente**, sem duplicatas, usando exclusivamente termos das **23 disciplinas pré-aprovadas** em `scripts/data/categories.json`:
  `Antropologia`, `Artes`, `Astronomia`, `Biologia`, `Computação`, `Direito`, `Economia`, `Educação`, `Filosofia`, `Física`, `Geografia`, `História`, `Linguística`, `Literatura`, `Matemática`, `Medicina`, `Música`, `Poesia`, `Política`, `Psicologia`, `Química`, `Sociologia`, `Teologia`.
- Ramificações específicas (`Filosofia Antiga`, `Patrística`, `Petrus Ramus`) vão em `keywords` (em artigos), nunca em `categories`.

---

## 2. Hierarquia de Cabeçalhos e Estrutura do Corpo

- **H1 implícito no YAML**: o corpo Markdown **nunca** contém `# Título` (H1), pois o leitor gera o H1 a partir do `title` do YAML. O corpo começa diretamente em `## ...`.
- **Title Case obrigatório**: `title` no YAML e todos os cabeçalhos (`##`, `###`, `####`) usam **Title Case**, sendo **proibida CAIXA ALTA** (`## INTRODUÇÃO`, `### QUESTÃO VI`).
  - **Exceção única**: algarismos romanos (`## VIII`, `### Capítulo IV`) e siglas técnicas oficiais (`LLMs`, `DOI`, `IA`, `KJV`).
- **Negrito proibido em cabeçalhos**: nunca use `## **Título**` (o cabeçalho já tem peso semântico próprio).
- **Itálico permitido em cabeçalhos**: mantenha `*itálico*` quando estilístico/original (ex.: `## *Do Gênero*`, `### *Capítulo I: Da Doutrina*`).
- **Sem saltos hierárquicos**: use `##` → `###` → `####`. Não pule de `##` para `####` nem use `#####` para capítulos.
- **Sumário (TOC) do PDF original**: remova índices dinâmicos com número de página importados do PDF.
- **Parágrafos contínuos (*unwrapped*)**: cada parágrafo deve formar uma única linha contínua sem quebras artificiais de virada de página ou de coluna do PDF.
- **Parágrafos numerados**: em tratados clássicos, mantenha o padrão `N - ` no início da linha a partir do segundo parágrafo (`2 - O seu ensinamento...`).

---

## 3. Tipografia, Aspas, Intervalos e Citações

- **Aspas**:
  - **Padrão obrigatório**: aspas tipográficas curvas duplas `“...”` e simples `‘...’`.
  - **Elegância clássica**: guillemets `«...»` são permitidos em textos clássicos/literários ou citações eruditas conforme o estilo da obra.
  - **Proibido**: aspas retas `"` e `'` fora de blocos de código, links ou tags HTML.
- **Intervalos numéricos (Meia-risca `–`)**:
  - Use obrigatoriamente **meia-risca (`–`)**, nunca hífen (`-`), em qualquer intervalo numérico de anos, páginas, linhas ou versículos:
  - ✅ `1510–1562`, `pp. 101–112`, `325 b–c`, `Jo 1.1–14`.
  - ❌ `1510-1562`, `pp. 101-112`, `Jo 1.1-14`.
- **Reticências tipográficas (`…`)**:
  - Padrão obrigatório: caractere único Unicode **`…` (`U+2026`)**; proibido usar três ou mais pontos ASCII (`...`, `....`, `. . .`) fora de blocos de código, matemática, links ou YAML.
  - Em omissões após fim de período em citações, use `. …` (ponto final + espaço + `…`), nunca `....` nem `. ...`.
- **Listas (Compatibilidade com o leitor Leia-me)**:
  - Toda lista (ordenada ou não ordenada, de nível principal ou **sublista aninhada**) **deve** ser separada por **uma linha em branco** do texto imediatamente acima — inclusive entre um item pai e sua sublista (ex.: `3. Texto:\n\n   - **2** ...`) e ao retornar de uma sublista ao nível externo.
  - Em sublistas aninhadas sob itens ordenados separados por linha em branco, alinhe a indentação à largura do marcador pai (`3` espaços para `1.`–`9.`, `4` espaços para `10.`–`99.`, `5` espaços para `100.`+) para preservar o aninhamento em CommonMark.
- **Diálogos e *Disputatio***:
  - Diálogos: interlocutor em Title Case ou sigla canônica seguido de travessão espaçado (`Agostinho — `, `Razão — `, `A. — `, `R. — `).
  - *Disputatio*: objeção em blockquote `> *Objeção...*` seguida de `**Resposta**:`.
- **Citações**:
  - Curtas (em linha): permanecem no parágrafo com `“...”` ou `«...»`.
  - Longas (destacadas ou > 3 linhas): use bloco `> ` isolado por linha em branco antes e depois.
  - Versos/dísticos poéticos intercalados: oração introdutória permanece no parágrafo anterior; versos vão em `> *...*` com dois espaços (`  `) ao final do verso para preservar a quebra poética.
- **Línguas estrangeiras e termos técnicos**: destaque em `*itálico*` termos em latim, grego, hebraico ou estrangeirismos não dicionarizados e títulos de obras (*De Imitatione Christi*). Use `**negrito**` apenas para definições ou ênfases conceituais fortes no corpo do texto.
- **Referências bíblicas (Opção B — Arábicos + Preservação da Forma)**:
  - **Preservar a forma do texto**: mantenha abreviado (`Jo 3.16`, `Hb 11.1`, `1Co 15.3–4`), por extenso (`João 3.16`, `Hebreus 11.1`, `1 Coríntios 15.3–4`, `Salmo 23.1`, `Salmos 119.105`) ou narrativo (`A Segunda Carta aos Coríntios 2.1`) conforme a prosa original.
  - **Normalizar apenas o que sai do padrão**:
    - Abreviações: 2 letras `Xx` (1ª maiúscula, 2ª minúscula, sem ponto final) e algarismo arábico colado (`HB` / `Heb.` → `Hb`, `Mat.` → `Mt`, `1 Co` / `I Co` → `1Co`);
    - Por extenso: apenas inicial maiúscula e algarismo arábico separado (`joão` → `João`, `HEBREUS` → `Hebreus`, `1Coríntios` / `I Coríntios` → `1 Coríntios`);
    - Separador capítulo/versículo sempre com **ponto** (`.`) e intervalos sempre com **meia-risca** (`–`): `Gn 1.26`, `Sl 119.105`, `Jo 1.1–14`, `Rm 3.23`, `1Co 15.3–4`.

---

## 4. Paginação Crítica, Âncoras (Padrão ABNT) e Aparato de Notas

### 4.1. Posicionamento da Âncora — Padrão ABNT/Português (Inviolável)
- A âncora fica **colada imediatamente à palavra, expressão ou aspas de fechamento, ANTES do sinal de pontuação**, sem espaço antes da âncora:
  - ✅ `...e a vítima trágica de suas maquinações[^1].`
  - ✅ `...sobre os “pressupostos comuns”[^nt1], segundo Aristóteles.`
  - ✅ `...cf. edições críticas, etc.[^2]` *(exceção apenas quando o ponto faz parte de abreviação como `etc.`, `a.C.`, `d.C.`, `Cf.`)*.
  - ❌ `...suas maquinações.[^1]` *(proibido após ponto/vírgula final)*.
  - ❌ `...suas maquinações [^1].` *(proibido espaço antes da âncora)*.

### 4.2. Namespaces Estritos de Notas
- **`[^1]`, `[^2]`, ...**: estritamente para **Notas do Autor** (100% literais e fiéis de `1` a `N` ao original; nunca renumere nem suprima).
- **`[^nt1]`, `[^nt2]`, ...**: estritamente para **Notas do Tradutor** (glosas filológicas, termos gregos/latinos). Como já são agrupadas sob `### Notas do Tradutor`, dispensa-se o prefixo redundante `**N. do T.**:`.
- **`[^ne1]`, `[^ne2]`, ...**: estritamente para **Notas Editoriais** (paginação canônica, proveniência, mini-bio do tradutor primário).
- A numeração dentro de cada namespace deve ser contínua a partir de 1 (`[^ne1]` antes de `[^ne2]`).

### 4.3. Rebaixamento de Âncoras e Paginação Crítica
- Notas originalmente presas ao título ou ao nome do autor (migrados para o YAML) devem ser rebaixadas ao **primeiro cabeçalho do corpo** (`## Introdução[^ne1][^ne2][^1]`).
- **Paginação crítica** (Bekker, Stephanus, Busse/CAG): padronize como `(Página. Linha)` (ex.: `(1. 1)`, `(2. 15)`) e documente a edição crítica em `[^ne1]`.

### 4.4. Estrutura do Pós-Texto (TOC do LeiaME)
Use **um único separador horizontal `---`** ao final do corpo do texto, seguido de subseções `###` por categoria e **uma linha em branco entre cada definição**:

```markdown
---

### Notas Editoriais

[^ne1]: **Paginação Canônica**: Referência à edição crítica de Adolf Busse (CAG IV.1, 1887).

[^ne2]: **Sobre o Tradutor**: Mini-biografia do tradutor primário quando aplicável.

### Notas do Tradutor

[^nt1]: O termo grego *axíōmata* (ἀξιώματα) designa proposições admitidas sem demonstração.

### Notas do Autor

[^1]: Aristóteles, *Categorias*, 1a 1–15b 32.
```
