# Observações Editoriais para Agentes de IA — OpenSciMD / IRSE

Este documento reúne lições práticas e armadilhas comuns identificadas no processo de conversão, extração e revisão editorial de documentos acadêmicos e e-books. Futuros agentes devem consultar estas notas ao revisar rascunhos.

---

## 1. Ruídos Comuns de Extração de PDF
- **Cabeçalhos e Rodapés Repetidos**: Linhas com o nome da revista, autor ou título que aparecem no topo de cada página do PDF (ex: `Revista Viae Veritatis | ViVe`, `DUMPS | A PRÁTICA...`) vazam frequentemente para o meio dos parágrafos no Markdown bruto. **Devem ser identificadas e removidas por completo**.
- **Quebras Artificiais em Viradas de Página**: Quando uma frase ou citação bíblica atravessa a virada de página, palavras isoladas (como o sujeito, a data ou a citação) podem ficar truncadas em linhas separadas. Sempre recomponha a continuidade natural do parágrafo.
- **Títulos Fragmentados**: Títulos de seções longos no PDF podem ser extraídos com quebra de linha interna (ex: uma linha `## I. TÍTULO PARTE 1` e outra `## PARTE 2`). Unifique-os em uma única linha de cabeçalho coerente.

---

## 2. Atenção Crítica às Notas de Rodapé e Aparato Final (TOC)
- **Integridade e Correspondência Literal (1 a N)**: Toda e qualquer nota de rodapé presente no PDF original (da primeira à última, sem exceção) deve ser reproduzida **literal e integralmente**, preservando rigorosamente a numeração original `[^1]` a `[^N]`. Nunca suprima, sintetize ou renumere artificialmente as notas.
- **Rebaixamento de Âncoras do Título e Autor**: Quando notas de rodapé estiverem ancoradas no título ou no nome do autor (elementos que são migrados para o Frontmatter YAML e saem do corpo), **as âncoras correspondentes devem ser rebaixadas diretamente para o cabeçalho ou título de seção imediato no início do corpo** (ex: `## Introdução[^1][^2]`). Nunca as espalhe no meio de palavras dos parágrafos subsequentes.
- **Estrutura Limpa no Pós-texto (TOC)**: Utilize **apenas um único separador horizontal `---`** no final do corpo da obra. Abaixo dele, organize as notas em subseções com nível `###` (ex.: `### Notas Editoriais`, `### Notas do Tradutor`, `### Notas do Autor`). Isso garante que cada categoria apareça de forma organizada no Sumário (TOC) do leitor LeiaME sem criar separadores duplicados.
- **Notas Longas e Multi-Página**: Quando uma nota de rodapé no PDF original ultrapassa a página atual, motores de extração podem concatenar o final dessa nota com o início da nota seguinte ou vazar partes no corpo do texto. Verifique sempre o PDF para remontar o texto completo da nota correspondente.

---

## 3. Diretrizes de Frontmatter YAML
- **Exclusividade no YAML**: Todos os dados catalográficos, autoria, tradução (`translator`), data e licença residem **exclusivamente no Frontmatter YAML**. Não duplique linhas de crédito (ex.: `_Tradução de..._`) no corpo do texto Markdown.
- **Título e Resumo**: O título do artigo e o resumo (`summary`) devem residir no cabeçalho YAML e ser removidos do corpo Markdown, iniciando o texto diretamente em `## Introdução` ou na primeira seção. **Se o resumo estiver presente no original, coloque-o 100% integralmente no campo `summary` (sem resumos do resumo ou cortes).**
- **Autores Estruturados**: Sempre declare `authors` em formato de lista estruturada com `name`, `orcid`, `email` e `affiliation`.
- **Páginas Obrigatórias (`pages`)**: O campo `pages` é estritamente obrigatório para artigos (ex: `pages: "1-15"`).
- **Busca Ativa via DOI**: Caso os metadados (como ORCID, afiliação, volume, fascículo ou páginas) estejam incompletos no rascunho, o agente de IA **deve consultar a API do Zenodo (`https://zenodo.org/api/records/<recid>`) ou a web** através do DOI para recuperar a ficha catalográfica completa.
- **Formato de Data**: A data deve seguir estritamente o padrão ISO `YYYY-MM-DD` (ou notação histórica aproximada para clássicos, ex.: `c. 270 d.C.`).
- **Rigor de Validação**: Ao finalizar qualquer revisão, certifique-se de que o arquivo atenda a todas as regras do validador executando `uv run openscimd validate`.

---

## 4. Estilo Tipográfico, Cabeçalhos e Prosa
- **Cabeçalhos e Destaques**:
  - `## *Título em Itálico*` e `### *Subtítulo em Itálico*`: O itálico em títulos é **expressamente permitido e mantido** quando o documento original assim o destacar.
  - 🚫 **Negrito em Títulos**: É proibido utilizar `## **Título**`, pois o nível de cabeçalho já possui peso tipográfico visual suficiente.
- **Incorrupção da Tradução**: Em revisões de traduções existentes (com ou sem acesso ao texto-fonte), a IA **NÃO PODE reescrever, parafrasear, resumir ou modernizar o vocabulário do tradutor**. A atuação deve ser estritamente estrutural (metadados, cabeçalhos, aspas, itálicos técnicos, paginação).
- **Paginação Crítica e Nota Editorial Explicativa**: Notações marginais em rascunhos (ex: `[N]`, `**[N]**` da edição Bekker, Stephanus ou CAG/Busse) devem ser convertidas deterministicamente para o padrão `(Página. Linha)` (ex: `(1. 1)`, `(2. 15)`). Em toda obra clássica com paginação canônica, **deve-se incluir uma Nota Editorial explicativa** (`[^1]`) ancorada no primeiro cabeçalho da obra, detalhando a edição crítica de referência.
- **Referências Bíblicas**: Padronize sempre com a abreviação canônica brasileira e ponto separador: `Gl 1.10`, `1Pe 2.9`, `Hb 13.15`, `Ef 5.19`, `Cl 3.16`, `Mt 15.9`, `2Cr 29.25`.
- **Línguas Originais e Termos Técnicos**: Mantenha expressões em latim (*Ecclesia reformata, semper reformanda secundum Verbum Dei*, *vicarius*, *per se*, *quod quid sit*), grego (*psalmois*, *hymnois*, *ōdais*, *pneumatikois*, *ethelothrēskeia*) e hebraico sempre destacadas em `*itálico*`.
- **Estruturas de Disputatio / Diálogo**: Objeções ou proposições em debate devem ser formatadas com bloco de citação `> *Objeção...*` seguido da respectiva `**Resposta**:`.

---

## 5. Respeito ao Ciclo de Trabalho (`data/`)
- Mantenha a organização estrita das fases:
  - `data/draft/`: Matriz bruta (saída crua do `salopdoc`, rascunhos fornecidos). ⚠️ **ESTRITAMENTE IMUTÁVEL. A IA nunca deve editar ou sobrescrever arquivos nesta pasta.**
  - `data/review/`: Mesa de revisão e trabalho ativo. Qualquer comando para revisar um arquivo de `data/draft/` deve criar sua saída e operar em `data/review/<nome>.md`.
  - `data/ready/`: Arquivo final homologado e validado após conferência.
  - `content/articles/` ou `content/books/`: Destino de publicação final.
