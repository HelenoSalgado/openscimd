# Guia de Tradução, Conversão e Edição em Markdown para o OpenSciMD e LeiaME

Este guia estabelece o padrão editorial, filológico e estrutural para qualquer pessoa que deseje traduzir ou converter artigos científicos, tratados clássicos e e-books para o ecossistema **OpenSciMD** e para o aplicativo de leitura **LeiaME**.

### Fluxo Geral de Contribuição

1. **Geração Inicial via IA:** Utilize o modelo de linguagem de sua preferência com os [Prompts Recomendados (Apêndice)](#apêndice-prompts-recomendados-para-ia) para extrair os metadados e converter o PDF ou texto bruto para Markdown puro.
2. **Revisão Humana:** Valide a fidelidade textual, remova ruídos de diagramação e confira as notas de rodapé conforme as diretrizes deste guia.
3. **Envio dos Arquivos:** Envie o par de arquivos com o mesmo nome em *kebab-case*: o arquivo **`.md`** e o **`.pdf` original** correspondente (ex.: `reformas-filosoficas.md` e `reformas-filosoficas.pdf`).

---

## 1. Princípios Editoriais e Filológicos

* **Integralidade:** O texto-fonte é a autoridade absoluta. É terminantemente proibido resumir, condensar, expurgar, atenuar ou censurar trechos, títulos ou notas. Todo o conteúdo original deve ser transposto na íntegra.
* **Registro Formal:** Empregue português formal, culto e erudito, preservando a gravidade e o tom da obra (filosófica, teológica ou acadêmica). Evite modernizações anacrônicas ou simplificações coloquiais que descaracterizem o estilo e a densidade do original.
* **Rigor Terminológico:** Termos técnicos e conceitos fundamentais de uma dada disciplina devem seguir as convenções já consagradas na tradição acadêmica em língua portuguesa. Mantenha estabilidade e homogeneidade terminológica em todo o documento.
* **Vocabulário Fiel:** Se um vocábulo contemporâneo não capturar a precisão pretendida pelo autor histórico, prefira o termo vernáculo clássico/arcaico correspondente ou insira uma Nota do Tradutor (`[^N]`).
* **Preservação da Ambiguidade:** Não resolva ambiguidades conceituais do original por meio de preferências interpretativas pessoais. Onde o texto-fonte for aberto ou polissêmico, a tradução deve manter a mesma abertura.
* **Inviolabilidade:** A tradução não deve conter glosas, comentários ou interpolações explicativas no fluxo dos parágrafos. Quaisquer elucidações editoriais ou filológicas devem constar estritamente em notas de rodapé (`[^N]`).

---

## 2. Padrões Estruturais e Tipográficos

* **Parágrafos Contínuos (*Unwrapped*):** Cada parágrafo deve ser uma linha contínua de texto sem quebras duras manuais no meio das frases, separado do parágrafo seguinte por uma linha em branco.
* **Citações Longas:** Passagens com mais de três linhas ou destacadas no original devem ser formatadas como bloco de citação (`> `), antecedidas e sucedidas por uma linha em branco.
* **Ênfases e Termos Estrangeiros:** Use `*itálico*` para expressões em línguas clássicas (latim, grego, hebraico), títulos de obras e ênfases suaves. Use `**negrito**` para termos conceituais definidos com destaque forte pelo autor.
* **Notas de Rodapé (`[^N]`):**
  * A âncora `[^N]` deve ficar colada à palavra ou pontuação correspondente, sem espaço (ex.: `termo.[^1]`).
  * A sequência numérica deve ser contínua de `[^1]` a `[^N]`, sem omissões ou saltos.
  * Todas as notas são declaradas no final do documento, precedidas por uma linha horizontal (`---`), com uma linha em branco entre cada nota:
    ```markdown
    ---

    [^1]: Conteúdo integral da nota aqui.

    [^2]: Nota do Tradutor: Esclarecimento filológico sobre o termo grego.
    ```
* **Cabeçalho de Metadados (YAML):** Todo arquivo deve iniciar obrigatoriamente na Linha 1 com delimitadores `---`. Os modelos completos de metadados estão inseridos diretamente nos [Prompts Recomendados (Apêndice)](#apêndice-prompts-recomendados-para-ia).

---

## 3. Checklist Rápido de Qualidade

Antes de submeter sua contribuição, verifique se:

- [ ] Possui o arquivo `.md` finalizado e o `.pdf` original correspondente.
- [ ] Ambos os arquivos compartilham o mesmo nome em *kebab-case* (ex.: `minha-obra.md` e `minha-obra.pdf`).
- [ ] O arquivo inicia com os delimitadores YAML `---` contendo os metadados requeridos (veja os modelos no [Apêndice](#apêndice-prompts-recomendados-para-ia)).
- [ ] O texto está livre de quebras de linha manuais/duras dentro dos parágrafos.
- [ ] Citações longas estão em blocos (`> `).
- [ ] As notas `[^1]` a `[^N]` correspondem integralmente às do original, sem omissões.

---

## Apêndice: Prompts Recomendados para IA

Envie o prompt abaixo ao modelo de IA junto com o PDF ou texto bruto do material original. Os modelos de metadados YAML já estão embutidos em cada prompt:

### A. Prompt para Artigos Acadêmicos e Científicos

```text
Você é um editor de artigos acadêmicos e científicos, extraia todas as informações de metadados disponíveis e converta o texto para Markdown com originalidade e precisão, sem nunca resumir, mas integralmente, usando o português formal e erudito quando as circunstâncias o exigem. O formato do texto e arquivo resultante deve ser um Markdown bem estruturado e com frontmatter tal qual o exemplo abaixo. O Markdown deve estar dentro de um bloco de código. As notas também, se houverem, devem estar bem estruturadas e referenciadas no rodapé no formato [^N].

Exemplo de metadados a ser seguido:

---
title: "REFORMAS FILOSÓFICAS DE PETRUS RAMUS: A SIMPLIFICAÇÃO DA LÓGICA E A SISTEMATIZAÇÃO DA METODOLOGIA"
journal: "History of Science"
volume: "6"
issue: "5"
pages: "101-112"
authors:
  - name: "Djamila Abdullazade"
    orcid: "0009-0007-5639-8512"
    email: "jamila.abdullazadee@gmail.com"
    affiliation: "Universidade Estatal de Baku"
  - name: "Aladdin Malikov"
    orcid: "0000-0001-5830-6764"
    email: "aladdin.malikov@gmail.com"
    affiliation: "AcademyGate Publishing"
summary: "O artigo analisa as concepções filosóficas e reformistas de Petrus Ramus, representante da época do Renascimento. Como um dos mais destacados reformadores do Renascimento, ele deixou um profundo legado. O artigo assinala que Ramus, graças às reformas que realizou tanto na pedagogia quanto na filosofia, exerceu significativa influência sobre o desenvolvimento do pensamento científico."

date: "20-06-2026"

UDC: "1(091):161/162"  
BBK: "87.3:87.4"  
HoS: "113"
DOI: "10.33864/2790-0037.2025.v6.i5.101-112"  

keywords: 
  - Renascimento  
  - Humanismo
  - Lógica
  - Lógica aristotélica
  - Metodização
  - Petrus Ramus

categories: 
  - Filosofia
  - Lógica

copyright: "AcademyGate Publishing"

license: "CC BY-NC 4.0"
---

### Diretrizes e Regras Especiais:
1. **Datação Histórica (`date`):** Refere-se à data de publicação do material original. Datas a.C devem ser impressas como tal, ignorando o padrão moderno.
2. **Rigor Filológico e Arcaísmos:** Se uma palavra usada na tradução do original não corresponde exatamente ao sentido pretendido pelo autor e existe uma forma mais arcaica, mas mais fiel ao sentido, prefira o correspondente mais arcaico para a palavra traduzida, ou adicione uma nota do tradutor, paralelamente, na sua própria sequência numérica às notas propriamente ditas, quando houverem.
3. **Citações Longas:** Para citações longas (destacadas no original ou que ultrapassem três linhas), utilize a formatação de citação em bloco do Markdown, antecedendo cada parágrafo ou linha da citação com o caractere `>`. Certifique-se de isolar a citação do corpo principal do texto com uma linha em branco antes e depois.
```

### B. Prompt para E-books e Tratados Clássicos

```text
Você é um editor de ebooks, extraia todas as informações de metadados disponíveis e converta o texto para Markdown com originalidade e precisão, sem nunca resumir, mas integralmente, usando o português formal e erudito quando as circunstâncias o exigem. O formato do texto e arquivo resultante deve ser um Markdown bem estruturado e com frontmatter tal qual o exemplo abaixo. O Markdown deve estar dentro de um bloco de código. As notas também, se houverem, devem estar bem estruturadas e referenciadas no rodapé no formato [^N], sem omissões e sem acréscimos.

Exemplo de metadados para eBooks:

---
title: "..."
author: "..."
summary: " ..."
date: "00-00-0000"
license: "..."
originalLanguage: "..."
language: "pt-BR"
translator: "Nome do Tradutor"
categories:
  - Filosofia
  - Teologia
---

### Diretrizes e Regras Especiais:
1. **Datação Histórica (`date`):** Refere-se à data de publicação do material original. Datas a.C devem ser impressas como tal, ignorando o padrão moderno.
2. **Rigor Filológico e Arcaísmos:** Se uma palavra usada na tradução do original não corresponde exatamente ao sentido pretendido pelo autor e existe uma forma mais arcaica, mas mais fiel ao sentido, prefira o correspondente mais arcaico para a palavra traduzida, ou adicione uma nota do tradutor, paralelamente, na sua própria sequência numérica às notas propriamente ditas, quando houverem.
3. **Citações Longas:** Para citações longas (destacadas no original ou que ultrapassem três linhas), utilize a formatação de citação em bloco do Markdown, antecedendo cada parágrafo ou linha da citação com o caractere `>`. Certifique-se de isolar a citação do corpo principal do texto com uma linha em branco antes e depois.
```
