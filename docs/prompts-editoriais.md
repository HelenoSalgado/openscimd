# Catálogo de Prompts Editoriais Recomendados para IA

Este documento reúne os **modelos de prompts oficiais e recomendados** para interagir com Agentes de IA no ecossistema OpenSciMD. Cada prompt foi elaborado para eliminar ambiguidades, reforçar a imutabilidade das matrizes em `data/draft/` e garantir fidelidade estrita às diretrizes editoriais do projeto ([`.agents/editorial/index.md`](file:///home/heleno/Documentos/GitHub/openscimd/.agents/editorial/index.md)).

---

## 🧭 Regras Gerais para Todos os Comandos de IA

1. **Imutabilidade de `data/draft/`**: Qualquer instrução de revisão lê o rascunho de `data/draft/` e gera sua saída ativa obrigatoriamente em `data/review/<nome>.md`.
2. **Incorrupção da Prosa**: A IA nunca deve reescrever, parafrasear, resumir ou modernizar o vocabulário de traduções humanas fornecidas. A atuação é estritamente estrutural e tipográfica.
3. **Cabeçalhos Semânticos**: O título principal H1 vai no Frontmatter YAML (`title`). Cabeçalhos no corpo usam `##` e `###`. Itálicos nos títulos são permitidos (`## *Título*`); negritos são proibidos (`## **Título**`).
4. **Notas de Rodapé Integrais**: Todas as notas `[^1]` a `[^N]` devem ser mantidas integrais e sem renumeração artificial.

---

## 📋 Contextos Operacionais e Modelos de Prompts

### Contexto 1: Saneamento e Formatação de Tradução / Rascunho sem Matriz Original
> **Cenário:** Você tem um rascunho de tradução em `data/draft/<arquivo>.md` (produzido por um tradutor humano ou fonte externa), sem o arquivo-fonte em língua original no repositório. O objetivo é sanitizar a formatação, adicionar o Frontmatter YAML, converter a paginação e salvar em `data/review/<arquivo>.md`.

```text
Atue de acordo com as diretrizes editoriais em @[.agents/editorial/index.md] e @[.agents/editorial/notas.md].

Execute o saneamento editorial do rascunho @data/draft/<nome-do-arquivo>.md, gerando o arquivo final revisado em data/review/<nome-do-arquivo>.md.

Diretrizes obrigatórias:
1. IMUTABILIDADE DO RASCUNHO: Mantenha data/draft/<nome-do-arquivo>.md 100% intocado. Salve o resultado exclusivamente em data/review/<nome-do-arquivo>.md.
2. INCORRUPÇÃO DA PROSA: Não altere, reescreva, resuma ou parafraseie nenhuma palavra da tradução. Preserve o vocabulário integral do tradutor (<Nome do Tradutor>) e todas as suas glosas explicativas entre colchetes [...].
3. FRONTMATTER YAML: Adicione o cabeçalho completo com title, author, summary (fiel ao escopo da obra), translator ("<Nome do Tradutor>"), originalLanguage ("<código ISO ex: el, la, en>"), language ("pt-BR"), date e license. Não adicione linhas redundantes de tradutor no corpo do texto (metadados residem exclusivamente no YAML).
4. CABEÇALHOS: Use ## para seções principais e ### para subseções. Mantenha os itálicos nos títulos caso existam (ex: ## *Do Gênero*). Nunca use negrito em títulos.
6. PAGINAÇÃO CRÍTICA E NOTAS EDITORIAIS: Converta todas as marcações de paginação clássica de [N] / **[N]** para a notação canônica (Página. Linha) [ex: (1. 1), (2. 15)]. Ancore as notas no primeiro cabeçalho (ex: ## *Introdução*[^1][^2]), onde [^1] explica a edição de referência da paginação canônica e [^2] apresenta a mini-bio do tradutor.
7. ESTRUTURA DE NOTAS (TOC): No final do documento, use um único separador horizontal --- e organize o aparato com cabeçalhos ### (ex: ### Notas Editoriais, ### Notas do Tradutor) para indexação limpa no Sumário.
```

---

### Contexto 2: Revisão e Auditoria de Tradução com Matriz em `data/raw/` (Anti-Alucinação 1:1)
> **Cenário:** Você possui o arquivo original em língua estrangeira em `data/raw/<arquivo>.md` e o rascunho traduzido em `data/draft/<arquivo>.md`. O objetivo é auditar a fidelidade semântica, eliminar lacunas e conferir parágrafo por parágrafo em `data/review/<arquivo>.md`.

```text
Atue como Auditor Filológico conforme @[.agents/editorial/prompt-revisao-ia.md] e @[.agents/editorial/fluxo-de-revisao-de-traducao.md].

Audite e revise o texto de @data/draft/<nome-do-arquivo>.md comparando-o rigorosamente contra o original em @data/raw/<nome-do-original>.md, gerando a saída em data/review/<nome-do-arquivo>.md.

Diretrizes obrigatórias:
1. CORRESPONDÊNCIA 1:1: Mapeie todas as seções e parágrafos do original para garantir que não haja omissões, saltos numéricos ou resumos silenciosos.
2. COMBATE A ALUCINAÇÕES: Inspecione termos técnicos, citações e argumentos complexos. Corrija qualquer paráfrase "suavizada" pela IA, restaurando o sentido literal do original.
3. FORMATAÇÃO DE DIÁLOGOS: Mantenha a pontuação canônica de interlocutores com travessão tipográfico (ex: AGOSTINHO — , RAZÃO — ).
4. REFERÊNCIAS E TERMOS: Padronize referências bíblicas no formato canônico brasileiro (ex: Jo 10.30, Rm 3.23) e termos originais em *itálico*.
5. FRONTMATTER: Preencha todos os campos canônicos incluindo originalLanguage ("la", "el", "en" ou "he").
```

---

### Contexto 3: Conversão e Digitalização de PDF de Artigo Acadêmico (Zenodo / DOI)
> **Cenário:** Um artigo acadêmico foi convertido a partir de PDF via `salopdoc` para `data/draft/<artigo>.md`. O objetivo é limpar ruídos de OCR, enriquecer metadados via DOI e preparar o arquivo para publicação.

```text
Atue conforme as diretrizes em @[.agents/editorial/index.md] e @[.agents/editorial/notas.md].

Revise o artigo acadêmico em @data/draft/<nome-do-artigo>.md, salvando a versão limpa em data/review/<nome-do-artigo>.md.

Diretrizes obrigatórias:
1. LIMPEZA DE RUÍDOS DE OCR: Remova cabeçalhos de página repetidos, números de página vazados e recomponha parágrafos partidos em viradas de página.
2. ENRIQUECIMENTO DE METADADOS: A partir do DOI constante no texto, pesquise ativamente no Zenodo ou na web para preencher a ficha catalográfica completa no Frontmatter YAML (authors com orcid, email e affiliation; journal; volume; issue; pages obrigatório; date; DOI; UDC; BBK; HoS; license).
3. RESUMO: Insira o resumo original 100% integralmente no campo summary do YAML e remova-o do corpo do texto.
4. REBAIXAMENTO DE NOTAS DE TÍTULO: Se houver notas de rodapé no título ou nos autores originais, rebaixe as âncoras para o primeiro cabeçalho do corpo (## Introdução[^1]).
5. NOTAS DE RODAPÉ (1 a N): Preserve todas as notas integralmente, sem renumeração artificial e declaradas ao final após ---.
6. VALIDAÇÃO: Ao finalizar, certifique-se de que o arquivo seja validável via `uv run openscimd validate`.
```

---

### Contexto 4: Edição de Livros e Tratados Clássicos em Partes e Capítulos
> **Cenário:** Edição de uma obra clássica dividida em livros, tratados ou capítulos com parágrafos numerados (ex: *A Imitação de Cristo*).

```text
Atue de acordo com @[.agents/editorial/exemplos/hierarquia-e-cabecalhos.md] e @[.agents/editorial/index.md].

Estruture e revise a obra clássica em @data/draft/<livro>.md, gerando a versão canônica em data/review/<livro>.md.

Diretrizes obrigatórias:
1. HIERARQUIA:
   - YAML title: Título da obra e do livro (ex: "A Imitação de Cristo: Livro I").
   - Nível ##: Título do Livro ou Parte Maior (ex: ## LIVRO PRIMEIRO: ADMOESTAÇÕES...).
   - Nível ###: Capítulos (ex: ### CAPÍTULO I).
   - Subtítulos de Capítulos: Em *itálico* na linha imediatamente abaixo ou integrados ao cabeçalho (### *Capítulo I: Do desprezo do mundo*). Nunca use negrito em títulos.
2. PARÁGRAFOS NUMERADOS: Mantenha a numeração no formato "N - " no início da linha contínua (ex: "2 - O seu ensinamento supera...").
3. REFERÊNCIAS BÍBLICAS: Padronize no formato canônico (ex: 1Co 15.54, Sl 119.105).
4. DESTINO: Grave em data/review/<livro>.md preservando data/draft/<livro>.md intocado.
```

---

### Contexto 5: Normalização Tipográfica e Ajustes Finos
> **Cenário:** O arquivo já está em `data/review/<arquivo>.md` e precisa de checagem final de regras tipográficas e estilísticas antes de ser movido para `data/ready/`.

```text
Revise o arquivo @data/review/<nome-do-arquivo>.md aplicando a normalização tipográfica final conforme @[.agents/editorial/exemplos/referencias-e-tipografia.md]:

1. ASPAS: Converta aspas retas ("...") para aspas curvas (“...” e ‘...’).
2. ÂNCORAS DE NOTA: Cole as âncoras na pontuação ou palavra precedente sem espaço (ex: palavra[^1], texto”[^2]).
3. TERMOS TÉCNICOS: Destaque expressões latinas, gregas e hebraicas em *itálico*.
4. CITAÇÕES EM BLOCO: Garanta que apenas citações longas usem > e que citações curtas permaneçam em linha com aspas curvas.
5. REFERÊNCIAS BÍBLICAS: Verifique a padronização com ponto separador de capítulo e versículo (ex: Jo 3.16).
```

---

## 🛠️ Comandos CLI Úteis para Apoio Editorial

| Ação | Comando |
| :--- | :--- |
| **Normalizar Referências Bíblicas** | `uv run openscimd normalize-refs "data/review/<arquivo>.md"` |
| **Auditoria de Tradução Matemática** | `uv run openscimd pipeline-review "data/raw/<orig>.md" "data/review/<rev>.md" --limit 10` |
| **Validar Metadados e Arquivos** | `uv run openscimd validate` |
| **Atualizar Índices e Buscas** | `uv run openscimd index` |
