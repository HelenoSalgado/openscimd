# 🎓 OpenSciMD - Open-Access Scientific Articles in Markdown

Bem-vindo ao **OpenSciMD**, um repositório centralizado projetado para o armazenamento, organização e compartilhamento de artigos acadêmicos e científicos estruturados em formato Markdown. 

O repositório conta com uma automação CLI construída em Python (gerenciada via `uv`) que extrai metadados acadêmicos (como DOI, UDC e Licenças) e compila automaticamente o índice geral para consumo por aplicações externas, além de prover um conjunto de ferramentas robustas para processamento, conversão e validação.

---

## 🚀 Como Funciona a Automação?

Nosso script de indexação analisa as pastas `articles` e `books` compilando todos os metadados do cabeçalho YAML para os arquivos `index-articles.json` e `index-books.json`.

### Principais Recursos:
* **CLI Integrado**: Todas as operações são feitas de maneira simplificada através do comando unificado `openscimd`.
* **Motor SalopDoc Integrado**: Extração tipográfica de PDFs com reflow semântico, detecção de frontmatter e normalização automática.
* **Preservação de IDs**: O script preserva IDs de artigos e livros pré-existentes, garantindo que referências antigas nunca sejam alteradas ou quebradas.
* **Estimação Inteligente de Leitura**: O tempo estimado de leitura é calculado baseando-se em uma velocidade média acadêmica de 200 palavras por minuto.
* **Automação de Capas e Assets**: Ferramentas nativas para injeção tipográfica avançada e geração de imagens otimizadas para todas as plataformas de acesso (mobile, tablet, desktop).
* **Geração de Arte via IA**: Interface de geração de arte com IA integrada diretamente no pipeline de criação de capas.
* **Motor RAG e SQLite Local**: Conector de busca textual de alta performance baseado em SQLite FTS5 com BM25, gerando blocos de contexto prontos para LLMs e pesquisa acadêmica offline.

---

## 📂 Estrutura do Repositório

* `content/articles/`: Artigos acadêmicos curados em formato Markdown.
* `content/books/`: Livros e tratados completos indexados no projeto.
* `assets/covers/`: Capas oficiais dos artigos em formato de imagem (grid responsivo: mobile, tablet, desktop).
* `assets/sources/`: Documentos-fonte originais normalizados (PDFs, HTMLs, etc.) disponíveis publicamente para consulta.
* `assets/desktop/` / `assets/images/`: Figuras e ilustrações internas dos artigos para o leitor.
* `data/raw/`: Fila de arquivos e PDFs brutos da web para processamento e ingestão preliminar (local).
* `data/draft/`: Rascunhos de Markdown gerados pelo SalopDoc aguardando revisão.
* `data/review/`: Fila de revisão editorial e colaborativa aberta a contribuições via Pull Request.
* `data/ready/`: Textos revisados e validados prontos para incorporação definitiva em `content/`.
* `scripts/`: Módulos em Python responsáveis pelas ferramentas de automação do projeto (`openscimd`).
* `docs/`: Documentações detalhadas de funcionamento do repositório.

---

## 🛠️ Execução e Desenvolvimento

O ambiente de execução e de gerenciamento de dependências deste projeto agora é totalmente baseado no `uv`. Certifique-se de ter o `uv` instalado em sua máquina. 

Para instalar as dependências, sincronizar o ambiente virtual e deixar tudo pronto para uso, execute na raiz do projeto:
```bash
uv sync
```

O comando oficial do projeto passa a ser `uv run openscimd`, que funciona como hub para todas as tarefas. Você pode obter ajuda global para qualquer comando digitando `uv run openscimd --help`.

### 1. Ingestão e Conversão de PDFs (SalopDoc)
Para converter um PDF original em Markdown rico com Frontmatter e reflow semântico:
```bash
uv run openscimd import-pdf data/raw/artigo.pdf
```

Para processar todos os PDFs brutos em lote de `data/raw/` para `data/draft/`:
```bash
uv run openscimd batch-import
```

Para normalizar a tipografia, aspas e estrutura de um Markdown legado:
```bash
uv run openscimd clean-md caminho/do/artigo.md
```

### 2. Atualizar o Índice Geral (`index-articles.json` e `index-books.json`)
Sempre que novos artigos, imagens ou PDFs forem adicionados, atualize os índices para a API:
```bash
uv run openscimd index
```

### 3. Validar Artigos e Metadados (Para Contribuintes)
Para verificar a formatação dos artigos e garantir a presença de todas as chaves obrigatórias no YAML, execute:
```bash
uv run openscimd validate
```

### 4. Gerar Capa de Artigo via IA (Recomendado: Google Gemini)
Gere automaticamente uma ilustração conceitual e integre a tipografia para a capa de um artigo usando a IA.
Configure primeiro as credenciais copiando e preenchendo o arquivo `.env`. E então:
```bash
uv run openscimd ai-cover <nome-do-artigo> ["estilo-opcional"] --provider gemini
```

### 5. Gestão e Tipografia de Capas
Para injetar os textos (títulos e autores) de forma vetorizada sobre uma imagem-base limpa:
```bash
uv run openscimd inject-text assets/covers/<nome-da-imagem>.png
```

Para processar as capas base injetadas garantindo dimensões e DPI corretos em todo o grid responsivo:
```bash
uv run openscimd build-covers
```

### 6. Ferramentas Editoriais Diversas
* `export-pdf`: Converte qualquer documento Markdown em PDF com tipografia clássica (EB Garamond/Cinzel/JetBrains Mono), paleta oficial LeiaME e box institucional de compilação.
  ```bash
  uv run openscimd export-pdf caminho/do/documento.md
  ```
* `verses`: Converte numerações e tópicos baseados em versículos para notação em sobrescrito.
* `review`: Utilitário ortográfico interativo de correção manual baseada num dicionário de arcaísmos embutido.

### 7. Motor RAG e Busca Local com IA
Compile a base de dados SQLite indexada por seções semânticas e tabelas virtuais FTS5:
```bash
uv run openscimd build-rag
```

Realize buscas contextuais instantâneas com snippets e caminhos dos arquivos físicos:
```bash
uv run openscimd search-rag "Sócrates justiça" --limit 5
```

Para gerar a saída formatada pronta para injeção no prompt de qualquer chat de IA / LLM:
```bash
uv run openscimd search-rag "Sócrates justiça" --ai
```

---

## 🤝 Como Contribuir

Toda contribuição acadêmica, editorial ou técnica é muito bem-vinda!

* **Revisões Textuais e Correções:** Para reportar erros ortográficos, falhas de OCR ou correções em livros e artigos, consulte nosso **[Guia de Contribuição (CONTRIBUTING.md)](CONTRIBUTING.md)** e abra uma **[Issue de Revisão Textual](https://github.com/helenosalgado/openscimd/issues/new?template=revisao_textual.yml)**.
* **Automações e Novos Artigos:** Se você deseja submeter novos artigos ou propor melhorias nas automações, consulte a documentação de apoio:
  1. **Entenda os Bastidores**: Leia o nosso guia de [Arquitetura e Funcionamento do Repositório](docs/arquitetura.md).
  2. **Saiba como Publicar**: Siga o passo a passo em [Fluxo de Trabalho e Contribuição](docs/fluxo-de-trabalho.md).
  3. **Diretrizes de Metadados**: Veja a lista de chaves YAML recomendadas para artigos científicos em [Diretrizes de Metadados Acadêmicos (MDC)](docs/metadata_guidelines.md).
  4. **Gerador de Capas e Identidade Visual**: Entenda as diretrizes estéticas e o funcionamento do criador automático em [Modelo e Geração de Capas](docs/gerador-de-capas.md).

---

## 📖 Como Citar o OpenSciMD

Se você utilizar este corpus, estrutura de dados, catálogos ou automações em seus projetos acadêmicos, teses, artigos científicos, experimentos de Processamento de Linguagem Natural (PLN/NLP), sistemas de busca semântica/RAG ou aplicações educacionais, por favor cite a obra conforme os modelos abaixo:

### BibTeX (LaTeX / Artigos Científicos / NLP)
```bibtex
@dataset{salgado2026openscimd,
  author       = {Heleno Salgado},
  title        = {{OpenSciMD}: Open-Access Scientific Articles in Markdown},
  year         = {2026},
  publisher    = {GitHub},
  version      = {1.0.0},
  url          = {https://github.com/HelenoSalgado/openscimd},
  note         = {Corpus acadêmico curado e estruturado em Markdown com enriquecimento de metadados}
}
```

### ABNT (Normas Brasileiras)
```text
SALGADO, Heleno. OpenSciMD: Open-Access Scientific Articles in Markdown. Versão 1.0.0. 2026. Disponível em: https://github.com/HelenoSalgado/openscimd.
```

### APA (7ª edição)
```text
Salgado, H. (2026). OpenSciMD: Open-Access Scientific Articles in Markdown (Version 1.0.0) [Data set]. GitHub. https://github.com/HelenoSalgado/openscimd
```

> **Dica:** O repositório possui integração nativa com o padrão de citação acadêmica do GitHub através do arquivo [CITATION.cff](CITATION.cff), disponível pelo botão **"Cite this repository"** na barra lateral.

---

## ⚖️ Licença e Direitos Autorais

O projeto **OpenSciMD** adota um modelo de licenciamento estratificado:

* **Compilação, Metadados, Capas e Código:** Licenciados sob a licença **[Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)](LICENSES.md)**. A redistribuição da obra completa é livre para fins não comerciais com atribuição obrigatória, sendo expressamente proibidas alterações indevidas, derivações da estrutura de dados ou exploração comercial.
* **Conteúdo Acadêmico dos Artigos:** Cada artigo e livro individual permanece sob a respectiva licença original concedida por seus autores ou editoras (ex: CC-BY, CC-BY-NC, Domínio Público), expressa no cabeçalho YAML de cada documento.

Para detalhes completos sobre termos e conformidade, consulte o documento **[LICENSES.md](LICENSES.md)**.
