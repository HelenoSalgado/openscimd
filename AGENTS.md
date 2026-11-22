# AGENTS.md — Contrato Operacional OpenSciMD

Este arquivo é o ponto de entrada obrigatório para qualquer agente de IA trabalhando neste repositório. Siga as regras abaixo sem desvios.

## 1. Regras Invioláveis

1. **Contenção Offline Textual (Autoridade Única Local)**
   - Durante transcrição, tradução ou revisão do corpo de uma obra, a única autoridade é a matriz local em `data/raw/` ou `assets/sources/`.
   - **Proibido** usar busca web (`search_web`, `read_url_content`) ou memória paramétrica para preencher lacunas, citações, versículos ou argumentos. Se a fonte local estiver ilegível ou truncada, pare e reporte ao usuário.
   - *Exceções*: (a) consulta a registros oficiais (Crossref/Zenodo/ORCID/periódicos) **estritamente** para campos bibliográficos do Frontmatter YAML (`DOI`, `ORCID`, `e_issn`, `pages`, `volume`, `issue`, `affiliation`); (b) pesquisa técnica de software/Python/Arch Linux para código e testes.
2. **Imutabilidade e Fonte Única da Verdade**
   - `data/raw/` e `data/draft/` são **estritamente imutáveis**. Nunca edite, sobrescreva ou apague arquivos dessas pastas.
   - Toda edição ativa ocorre exclusivamente em `data/review/` (inclusive quando uma obra já publicada em `content/` entra em re-revisão: copie-a via `openscimd start-review`).
   - Ao promover (`openscimd promote`), a obra vai para `content/` e a cópia ativa é removida de `data/review/`. Nunca publique diretamente em `content/` sem passar pelos gates e sem autorização explícita do usuário.
3. **Incorrupção Textual**
   - Zero paráfrases, resumos silenciosos, censura, omissões ou modernização de vocabulário de traduções humanas fornecidas.
4. **Proibição de Revisão Falsa ou Incompleta**
   - É proibido declarar um documento “revisado” ou “concluído” sem:
     1. Leitura e conferência **integral em blocos de 150–200 linhas** registradas no manifesto `<obra>.audit.md` (ver `.agents/03-line-by-line-review.md`);
     2. Execução com **0 erros** de:
        - `uv run openscimd validate --file <caminho> [--source <matriz>]`
        - `uv run openscimd review --check <caminho>` (analisado item a item).
5. **Ambiente Python Exclusivo via `uv`**
   - Use sempre `uv run ...`, `uv add ...` ou `uv sync`. Nunca use `pip` nem `uv pip install`.

---

## 2. Mapa de Ferramentas e Ordem Exata de Execução

| Etapa | Quando usar | Comando exato | Destino / Saída |
| :--- | :--- | :--- | :--- |
| **1a. Ingestão PDF (padrão)** | PDF digital com texto selecionável | `uv run openscimd import-pdf data/raw/<x>.pdf -o data/draft/<x>.md` | `data/draft/<x>.md` |
| **1b. Ingestão PDF (remoto/GPU Colab)** | PDF escaneado, fórmulas ou OCR complexo | `uv run openscimd remote-extract data/raw/<x>.pdf -o data/draft/ [--gpu T4]` | `data/draft/<x>.md` (Ver `docs/colab-integration.md`) |
| **1c. Ingestão HTML legado** | HTML antigo baseado em tabelas/Windows-1252 | `uv run openscimd clean-html data/raw/<x>.htm data/draft/<x>.md [-a "<Autor>"]` | `data/draft/<x>.md` |
| **1d. Ingestão HTML moderno** | HTML estruturado ou com frames | `uv run openscimd html-to-md data/raw/<x>.html data/draft/<x>.md` | `data/draft/<x>.md` |
| **2. Iniciar revisão** | Nova obra (`data/draft/`) ou re-revisão (`content/`) | `uv run openscimd start-review <origem> [--type articles\|books] [--dest <subcaminho>]` | `data/review/.../<x>.md` + `.audit.md` |
| **3. Enriquecer YAML** | Artigo com `DOI` no frontmatter | `uv run openscimd enrich data/review/<...>.md` | Atualiza YAML via Crossref/Zenodo |
| **4. Refs bíblicas** | Padronizar `Jo 3:16` / `HB 11:1` / `1Coríntios` | `uv run openscimd normalize-refs data/review/<...>.md` | Preserva forma e normaliza pontuação/siglas |
| **5. Checagem ortográfica** | Arcaísmos, grafia e Hunspell `pt_BR` | `uv run openscimd review --check data/review/<...>.md` | Relatório para inspeção humana/IA |
| **6. Revisão linha a linha** | Toda obra antes de validar/promover | Conferência manual em blocos de 150–200 linhas + `.audit.md` | Ver `.agents/03-line-by-line-review.md` |
| **7. Gate obrigatório** | Validar YAML + Linter Editorial + Fonte | `uv run openscimd validate --file data/review/<...>.md [--source <orig>]` | 0 erros para aprovar |
| **8. Promover** | Somente após aprovação explícita do usuário | `uv run openscimd promote data/review/<...>.md [--source <orig>] --index` | Move para `content/`, limpa `review/` e indexa |

> [!WARNING]
> Os comandos experimentais `translate-file`, `pipeline-review` e `check-translation` (baseados em MarianMT) estão em **redesign** e **não** substituem a conferência filológica nem devem ser usados como critério de aprovação.

---

## 3. Playbooks Modulares (Carregue Conforme a Tarefa)

- **Pipeline e comandos**: [`.agents/00-pipeline.md`](.agents/00-pipeline.md)
- **Especificação editorial única (YAML, tipografia, ABNT, notas)**: [`.agents/01-editorial-spec.md`](.agents/01-editorial-spec.md)
- **Protocolo de tradução filológica e bíblica**: [`.agents/02-translation-protocol.md`](.agents/02-translation-protocol.md)
- **Protocolo obrigatório de revisão linha a linha**: [`.agents/03-line-by-line-review.md`](.agents/03-line-by-line-review.md)
- **Design System de Capas (Artigos)**: [`.agents/editorial/design-system-capas-artigos.md`](.agents/editorial/design-system-capas-artigos.md)
- **Design System de Capas (Livros)**: [`.agents/editorial/design-system-capas-livros.md`](.agents/editorial/design-system-capas-livros.md)
