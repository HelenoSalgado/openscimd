# Diretrizes de Metadados Acadêmicos (MDC)

Este documento estabelece o padrão de metadados YAML (MDC keys) recomendado para a pasta `articles` no repositório de artigos científicos e acadêmicos. O uso de metadados padronizados otimiza a indexação, facilita o gerenciamento administrativo, melhora a busca e enriquece a experiência de leitura do usuário final.

---

## 📋 Chaves Atuais e Propostas

| Chave YAML | Tipo de Dado | Obrigatória | Descrição / Exemplo | Propósito Administrativo |
| :--- | :--- | :---: | :--- | :--- |
| **`title`** | String | Sim | `"A Metafísica na Modernidade"` | Identificação primária do artigo. |
| **`authors`** | Array | Sim | Lista de autores (ver seção de [Autores Estruturados](#-autores-estruturados-recomendado)) | Crédito acadêmico e busca por autor. |
| **`summary`** | String | Sim | Resumo sucinto do conteúdo. | Exibição de cards em portais de busca. |
| **`date`** | String (Date) | Sim | `"2026-06-18"` ou `"18-06-2026"` | Data de publicação ou envio original. |
| **`doi`** | String | Não | `"10.33864/2790-0037.2025.v6.i5.101-112"` | **Digital Object Identifier**: O padrão global para linkagem e citação científica persistente. |
| **`udc`** / **`UDC`** | String | Não | `"1(091):161/162"` | **Classificação Decimal Universal**: Organização temática padronizada internacionalmente. |
| **`bbk`** / **`BBK`** | String | Não | `"87.3:87.4"` | **Classificação Bibliotecária-Bibliográfica**: Usada para fins de indexação em bibliotecas. |
| **`hos`** / **`HoS`** | String | Não | `"113"` | Classificação acadêmica secundária / histórica. |
| **`license`** | String | Sim | `"CC BY-NC 4.0"` | Licença sob a qual o artigo está distribuído (CC BY-NC, CC BY, etc.). |
| **`journal`** | String | Não | `"Journal History of Science"` | Revista ou veículo de publicação original. |
| **`volume`** | String / Int | Não | `"6"` | Volume da publicação da revista. |
| **`issue`** | String / Int | Não | `"5"` | Edição ou número da publicação da revista. |
| **`pages`** | String | Não | `"101-112"` | Páginas onde o artigo foi publicado no original. |
**`e_issn`** | String | Não | `"1982-5587"` | Identificar a revista no âmbito digital.
| **`pdf_url`** | String | Não | `"/pdfs/reformas-filosoficas.pdf"` | Link para a versão formatada em PDF. |
| **`language`** | String (ISO) | Não | `"pt"`, `"en"`, `"es"` | Código do idioma principal do texto. |
| **`keywords`** | Array | Não | `["Lógica", "Renascimento", "Metodologia"]` | Palavras-chave de indexação adicionais. |

---

## 👥 Autores Estruturados

```yaml
authors:
  - name: "Djamila Abdullazade"
    orcid: "0009-0007-5639-8512"
    email: "jamila.abdullazadee@gmail.com"
    affiliation: "Universidade Estatal de Baku"
  - name: "Aladdin Malikov"
    orcid: "0000-0001-5830-6764"
    email: "aladdin.malikov@gmail.com"
    affiliation: "AcademyGate Publishing"
```

---

## 🛠️ Como Adicionar Novos Artigos

Sempre que adicionar um novo arquivo `.md` na pasta `articles`, preencha o bloco inicial (frontmatter) seguindo este modelo completo:

```yaml
---
title: "TÍTULO DO SEU ARTIGO"
authors:
  - "Autor 1"
  - "Autor 2"
summary: "Um breve resumo sobre a pesquisa desenvolvida no artigo."
date: 20-06-2026
categories:
  - Categoria A
  - Categoria B
license: "CC BY 4.0"
UDC: "Código UDC"
BBK: "Código BBK"
DOI: "Link ou identificador DOI"
journal: "Nome da Revista Científica"
volume: 1
issue: 2
pages: "10-25"
language: "pt"
---
```

Após adicionar o artigo, execute o script de indexação no seu terminal:

```bash
node scripts/update-index.js
```

O script irá ler os metadados novos, recalcular o tempo estimado de leitura (com velocidade ajustada para leitura técnica) e incluir o link da imagem da capa de forma totalmente automatizada.
