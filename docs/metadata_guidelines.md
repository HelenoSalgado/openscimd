# Diretrizes de Metadados Acadêmicos (MDC)

Este documento estabelece o padrão de metadados YAML obrigatório para artigos (`content/articles/`) e e-books (`content/books/`) no **OpenSciMD**.

---

## 📋 Chaves de Metadados

| Chave YAML | Tipo | Obrigatória | Descrição / Exemplo | Propósito |
| :--- | :--- | :---: | :--- | :--- |
| **`title`** | String | Sim | `"A Metafísica na Modernidade"` | Título em *Title Case* (H1 implícito). |
| **`authors`** / **`author`** | Array / String | Sim | Lista estruturada em artigos; string ou lista em livros | Crédito acadêmico e busca por autor. |
| **`summary`** | String | Sim | Resumo integral do artigo ou sinopse do livro | Exibição em cards e catálogo. |
| **`date`** | String | Sim | `"2026-06-18"` ou ABNT (`"20 nov. 2025"`, `"20-11-2025"`); histórico em livros (`"399 a.C."`) | Data canônica de publicação original. |
| **`language`** | String | Sim | `"pt-BR"` ou `"pt-PT"` | Variante de língua portuguesa da edição. |
| **`originalLanguage`** | String | Recomendada | `"en"`, `"la"`, `"el"`, `"he"` | Idioma da matriz-fonte em `data/raw/` usada na tradução. |
| **`translator`** | String | Se traduzido | `"Nome do Tradutor"` | Crédito exclusivo no YAML (não repetir no corpo). |
| **`categories`** | Array | Sim | `["Filosofia", "História"]` | Apenas disciplinas canônicas pré-aprovadas, em ordem alfabética. |
| **`keywords`** | Array | Só artigos | `["Lógica", "Renascimento", "Petrus Ramus"]` | Indexação temática específica (**proibido em livros**). |
| **`license`** | String | Sim | `"CC BY 4.0"`, `"CC BY-NC 4.0"`, `"Domínio Público"` | Licença de distribuição da obra. |
| **`pages`** | String | Sim (artigos) | `"101–112"` ou `"1–15"` | Intervalo de páginas na publicação original (com meia-risca). |
| **`DOI`** | String | Recomendada | `"10.33864/2790-0037.2025.v6.i5.101-112"` | Identificador persistente para `openscimd enrich`. |
| **`journal`** | String | Recomendada | `"History of Science"` | Periódico ou revista científica de origem. |
| **`volume`** / **`issue`** | Int / String | Se periódico | `volume: 6`, `issue: 5` | `volume` deve coincidir com a pasta `vol-{N}`. |
| **`e_issn`** | String | Recomendada | `"1982-5587"` | ISSN eletrônico do periódico. |
| **`UDC`** / **`BBK`** / **`HoS`** | String | Opcional | `"1:94"` / `"87.3:87.4"` / `"113"` | Códigos biblioteconômicos (CDU derivada se ausente). |

---

## 🏷️ Diretriz Estrita de Categorias

Adota-se o **Princípio da Separação Semântica**:

1. **`categories` (Disciplinas Canônicas Gerais)**:
   - Contém apenas grandes áreas do conhecimento (substantivos simples, nunca termos compostos como `Filosofia Antiga`).
   - A lista deve estar **ordenada alfabeticamente** e sem duplicatas.
   - Use sempre `categories` no plural (`category` é obsoleto).
2. **`keywords` (Exclusivo para Artigos)**:
   - Recebe especializações, períodos e nomes próprios (`Patrística`, `Estoicismo`, `Petrus Ramus`).
   - E-books (`content/books/`) **não podem** conter `keywords`.

### Lista Pré-Aprovada das 23 Disciplinas Aceitas (`scripts/data/categories.json`)

- **Antropologia** (`39`)
- **Artes** (`7`)
- **Astronomia** (`52`)
- **Biologia** (`57`)
- **Computação** (`004`)
- **Direito** (`34`)
- **Economia** (`33`)
- **Educação** (`37`)
- **Filosofia** (`1`)
- **Física** (`53`)
- **Geografia** (`91`)
- **História** (`94`)
- **Linguística** (`81`)
- **Literatura** (`82`)
- **Matemática** (`51`)
- **Medicina** (`61`)
- **Música** (`78`)
- **Poesia** (`82-1`)
- **Política** (`32`)
- **Psicologia** (`159.9`)
- **Química** (`54`)
- **Sociologia** (`316`)
- **Teologia** (`2`)

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

## 🔍 Comandos de Validação, Lint e Indexação

```bash
# Validar um arquivo em revisão (metadados + linter editorial + fonte)
uv run openscimd validate --file "data/review/articles/revista/vol-1/artigo.md" --source "data/raw/artigo.pdf"

# Executar linter editorial em arquivo ou diretório
uv run openscimd lint "data/review/" --strict

# Validar todo o catálogo publicado
uv run openscimd validate --target all

# Atualizar índices JSON e validar ledger de IDs
uv run openscimd index
uv run openscimd validate-ids --base-ref HEAD
```
