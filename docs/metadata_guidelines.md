# Diretrizes de Metadados Acadêmicos (MDC)

Este documento estabelece o padrão de metadados YAML (MDC keys) obrigatório para os artigos (`content/articles`) e e-books (`content/books`) no OpenSciMD. O uso de metadados padronizados otimiza a indexação, facilita o gerenciamento administrativo, melhora a busca e enriquece a experiência de leitura do usuário final.

---

## 📋 Chaves de Metadados

| Chave YAML | Tipo de Dado | Obrigatória | Descrição / Exemplo | Propósito Administrativo |
| :--- | :--- | :---: | :--- | :--- |
| **`title`** | String | Sim | `"A Metafísica na Modernidade"` | Identificação primária da obra. |
| **`authors`** | Array | Sim* | Lista de autores (ver seção de [Autores Estruturados](#-autores-estruturados-recomendado)) | Crédito acadêmico e busca por autor (*ou `author` no singular em livros). |
| **`summary`** | String | Sim | Resumo sucinto do conteúdo. | Exibição de cards em portais de busca. |
| **`date`** | String (Date) | Sim | `"2026-06-18"`, `"18-06-2026"` ou ano histórico | Data canônica de publicação original. |
| **`categories`** | Array | Sim | `["Filosofia", "História"]` | **Disciplinas canônicas generalistas pré-aprovadas** (ver [Diretriz de Categorias](#-diretriz-estrita-de-categorias)). |
| **`keywords`** | Array | Não | `["Lógica", "Renascimento", "Metodologia"]` | Palavras-chave, períodos históricos, correntes e temas específicos. |
| **`license`** | String | Sim | `"CC BY-NC 4.0"` ou `"Domínio Público"` | Licença editorial sob a qual o texto está distribuído. |
| **`pages`** | String | Sim (artigos) | `"101-112"` ou `"1-15"` | Intervalo de páginas na publicação original. |
| **`DOI`** | String | Não | `"10.33864/2790-0037.2025.v6.i5.101-112"` | Identificador persistente digital global. |
| **`udc`** / **`UDC`** | String | Não | `"1(091):161/162"` | Classificação Decimal Universal. |
| **`bbk`** / **`BBK`** | String | Não | `"87.3:87.4"` | Classificação Bibliotecária-Bibliográfica. |
| **`journal`** | String | Não | `"Journal History of Science"` | Revista ou veículo de publicação original. |
| **`volume`** | String / Int | Não | `"6"` ou `1` | Volume da publicação da revista. |
| **`issue`** | String / Int | Não | `"5"` | Edição ou número da publicação da revista. |
| **`e_issn`** | String | Não | `"1982-5587"` | ISSN eletrônico do periódico. |
| **`language`** | String (ISO) | Não | `"pt-BR"`, `"pt"`, `"en"` | Código do idioma do texto. |

---

## 🏷️ Diretriz Estrita de Categorias

Para simplificar brutalmente e ordenar com precisão taxonômica o acervo, adota-se o **Princípio da Separação Semântica**:

1. **`categories` (Disciplinas Canônicas Gerais):**
   - Deve conter **apenas** grandes áreas e disciplinas acadêmicas reconhecidas.
   - **Termos Não Compostos:** Sempre substantivos puros (ex: `Filosofia`, e **não** `Filosofia Antiga`; `História`, e **não** `História da Educação`).
   - **Ordenação Alfabética:** A lista no YAML deve estar **sempre ordenada alfabeticamente** (ex: `["Educação", "História"]`).
   - **Chave Canônica:** Use sempre a chave no plural `categories`. O uso de `category` no singular é obsoleto.

2. **`keywords` (Indexação Temática Específica):**
   - Absorve ramificações, escolas de pensamento, períodos cronológicos e metodologias (ex: `Filosofia Antiga`, `Patrística`, `Estoicismo`, `Petrus Ramus`, `Processo de Sócrates`, `Modelos de Linguagem`, `Salmodia Exclusiva`).

### Lista Pré-Aprovada de Disciplinas Aceitas

Apenas as seguintes 22 categorias são aceitas pelo validador do repositório:

- **Antropologia**
- **Artes**
- **Astronomia**
- **Biologia**
- **Computação**
- **Direito**
- **Economia**
- **Educação**
- **Filosofia**
- **Física**
- **Geografia**
- **História**
- **Linguística**
- **Literatura**
- **Matemática**
- **Medicina**
- **Música**
- **Política**
- **Psicologia**
- **Química**
- **Sociologia**
- **Teologia**

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

## 🛠️ Exemplo Completo de Frontmatter

```yaml
---
title: "A Metafísica na Modernidade"
authors:
  - name: "Nome do Autor"
    affiliation: "Instituição de Pesquisa"
summary: "Um breve resumo sobre a pesquisa desenvolvida no artigo."
date: "2026-06-20"
categories:
  - Filosofia
  - História
keywords:
  - Metafísica
  - Racionalismo
  - Século XVII
license: "CC BY 4.0"
pages: "10-25"
language: "pt-BR"
---
```

---

## 🔍 Comandos de Validação e Indexação

```bash
# Validar artigos e e-books
uv run openscimd validate

# Validar especificamente artigos
uv run openscimd validate --target articles

# Validar especificamente e-books
uv run openscimd validate --target books

# Atualizar os índices JSON (index-articles.json e index-books.json)
uv run openscimd index
```
