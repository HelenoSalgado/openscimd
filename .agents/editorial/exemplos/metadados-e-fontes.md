# Guia de Metadados YAML e Identificação de Fontes

Este documento exemplifica as regras para preenchimento de metadados no Frontmatter YAML, especialmente sobre a determinação correta do campo `originalLanguage`.

---

## 1. O Campo `originalLanguage` (Matriz Textual vs. Língua Histórica)

No ecossistema OpenSciMD, o campo **`originalLanguage`** refere-se estritamente ao **idioma do arquivo-fonte bruto utilizado para a tradução no projeto** (armazenado em `data/raw/`).

### Exemplos Práticos:

1. **Obra clássica traduzida a partir de uma matriz em Inglês:**
   * Caso: *A Imitação de Cristo* (Tomás de Kempis escreveu em latim no séc. XV, mas a matriz do projeto é a tradução em inglês de William Benham em `data/raw/The Imitation of Christ.md`).
   * Valor correto: `originalLanguage: "en"`

2. **Obra clássica traduzida diretamente do Latim:**
   * Caso: *Solilóquios de Santo Agostinho* (traduzido diretamente do texto latino em `data/raw/LogicMuseum_Soliloquia_Liber_I.html`).
   * Valor correto: `originalLanguage: "la"`

3. **Texto bíblico traduzido a partir da King James Bible de 1611:**
   * Valor correto: `originalLanguage: "en"`

4. **Tratado traduzido diretamente do Grego:**
   * Valor correto: `originalLanguage: "el"`

---

## 2. Modelos Completos de Frontmatter YAML

### A. Para Livros e Obras Clássicas (`content/books/`)

```yaml
---
title: "A Imitação de Cristo: Livro I"
author: "Thomas à Kempis"
summary: "Tratado clássico de espiritualidade cristã, composto de quatro livros de admoestações espirituais, que exorta o leitor ao desprezo do mundo, ao conhecimento de si mesmo, à humildade e à imitação da vida de Cristo como caminho de perfeição interior."
date: "1418 d.C."
originalLanguage: "en"
language: "pt-BR"
translator: "Heleno Salgado"
license: "Domínio Público"
categories:
  - Teologia
  - Espiritualidade
---
```

### B. Para Artigos Científicos (`content/articles/`)

```yaml
---
title: "REFORMAS FILOSÓFICAS DE PETRUS RAMUS: A SIMPLIFICAÇÃO DA LÓGICA E A SISTEMATIZAÇÃO DA METODOLOGIA"
authors:
  - name: "Djamila Abdullazade"
    orcid: "0009-0007-5639-8512"
    email: "jamila.abdullazadee@gmail.com"
    affiliation: "Universidade Estatal de Baku"
  - name: "Aladdin Malikov"
    orcid: "0000-0001-5830-6764"
    email: "aladdin.malikov@gmail.com"
    affiliation: "AcademyGate Publishing"
summary: "O artigo analisa as concepções filosóficas e reformistas de Petrus Ramus, representante da época do Renascimento..."
date: "2026-06-20"
journal: "History of Science"
volume: 6
issue: 5
pages: "101-112"
DOI: "10.33864/2790-0037.2025.v6.i5.101-112"
UDC: "1(091):161/162"
BBK: "87.3:87.4"
HoS: "113"
language: "pt"
license: "CC BY-NC 4.0"
categories:
  - Filosofia
  - Lógica
keywords:
  - Renascimento
  - Humanismo
  - Petrus Ramus
---
```
