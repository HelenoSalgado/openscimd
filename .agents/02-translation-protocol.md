# 02 — Protocolo de Tradução Filológica e Bíblica

Este documento rege todas as tarefas de tradução para **Português Formal e Erudito** (`pt-BR` ou `pt-PT` conforme a obra) no OpenSciMD.

---

## 1. Os 10 Princípios Gerais de Tradução

1. **Primazia absoluta do texto-fonte local**: A matriz em `data/raw/` (ou `assets/sources/`) é a autoridade máxima. Toda decisão deve ser justificável pelo texto original; nunca substitua por memória paramétrica ou versões externas da web.
2. **Fidelidade literal e estrutural**: Preserve o sentido literal, o encadeamento lógico das orações e a estrutura dos parágrafos. Intervenha na ordem sintática apenas quando a gramática do português exigir.
3. **Alinhamento 1:1 de estrutura**: Capítulos, seções, diálogos e notas são parte da obra. Não funda, divida arbitrariamente nem desloque blocos de conteúdo.
4. **Registro e estilo solene**: Use português formal, clássico e estável, adequado a textos acadêmicos, filosóficos, patrísticos ou bíblicos. Evite modernismos ou coloquialismos que rebaixem a gravidade da obra.
5. **Conservação de conectivos e paralelismos**: Preserve partículas recorrentes (“E”, “Então”, “Mas”, “Pois”, “Assim”), repetições e fórmulas estilísticas; não as elimine como “redundâncias”.
6. **Ausência de comentário no corpo**: Traduza, não comente nem interprete dentro do parágrafo. Qualquer esclarecimento filológico vai para Nota do Tradutor (`[^ntN]`).
7. **Preservação da ambiguidade**: Onde o texto original é polissêmico ou aberto, mantenha a abertura em português em vez de impor uma interpretação fechada.
8. **Coerência terminológica (Glossário da Obra/Série)**: Escolhido um termo em português para um conceito técnico ou nome próprio (ex.: `Eutífron`, `aliança`, `iniquidade`, `substância`), mantenha-o idêntico em toda a obra e em todos os fascículos do mesmo volume. Registre escolhas críticas em um glossário local ou em `[^ntN]`.
9. **Transparência diante de incerteza**: Se houver dúvida real sobre segmentação ou trecho ilegível na matriz local, sinalize explicitamente ao usuário; nunca invente nem complete silenciosamente.
10. **Autocorreção integral**: Antes de entregar qualquer bloco traduzido, confronte-o sentença a sentença contra o original.

---

## 2. Regras Específicas para Textos Bíblicos

Ao traduzir livros bíblicos:
- **Versículos intactos**: Cada versículo traduzido deve corresponder exatamente ao versículo de origem, sem saltos, fusões ou deslocamento entre capítulos.
- **Cadência e conjunções iniciais**: Preserve rigorosamente o ritmo paratático e as conjunções iniciais características do texto sagrado.
- **Zero glosa doutrinária**: Nunca insira explicações teológicas no corpo dos versículos.

---

## 3. Regra de Contenção vs. Exceções Autorizadas

| Domínio | Regra de Acesso Externo |
| :--- | :--- |
| **Corpo do texto / Citações / Diálogos / Notas do autor** | **100% OFFLINE**. Proibido `search_web` ou memória paramétrica para reconstituir trechos. |
| **Catalogação YAML (`DOI`, `ORCID`, `e_issn`, `pages`, `affiliation`)** | Permitido consultar Crossref, Zenodo, ORCID e página do periódico quando ausente da matriz local. |
| **Engenharia de código (`scripts/`, `tests/`, CLI, Arch Linux)** | Pesquisa técnica plena autorizada. |
