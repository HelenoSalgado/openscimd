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

---

## 📂 Estrutura do Repositório

* `content/articles/`: Artigos acadêmicos escritos em Markdown.
* `content/books/`: Livros completos indexados no projeto.
* `assets/covers/`: Capas oficiais dos artigos em formato de imagem.
* `assets/pdfs/`: Versão original dos artigos e livros em formato PDF.
* `assets/images/`: Imagens auxiliares e mídia genérica.
* `data/raw/`: Fila de PDFs brutos para processamento e ingestão.
* `data/draft/`: Rascunhos de Markdowns gerados automaticamente pelo SalopDoc.
* `scripts/`: Módulos em Python responsáveis pelas ferramentas de automação do projeto.
* `legacy_scripts/`: Histórico com scripts antigos Node.js e Shell Script do projeto.
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
uv run openscimd import-pdf assets/pdfs/artigo.pdf
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
* `verses`: Converte numerações e tópicos baseados em versículos para notação em sobrescrito.
* `review`: Utilitário ortográfico interativo de correção manual baseada num dicionário de arcaísmos embutido.

---

## 🤝 Como Contribuir

Toda contribuição acadêmica ou técnica é muito bem-vinda! Se você deseja submeter novos artigos ou propor melhorias nas automações, por favor consulte a nossa documentação de apoio:

1. **Entenda os Bastidores**: Leia o nosso guia de [Arquitetura e Funcionamento do Repositório](docs/arquitetura.md).
2. **Saiba como Publicar**: Siga o passo a passo em [Fluxo de Trabalho e Contribuição](docs/fluxo-de-trabalho.md).
3. **Diretrizes de Metadados**: Veja a lista de chaves YAML recomendadas para artigos científicos em [Diretrizes de Metadados Acadêmicos (MDC)](docs/metadata_guidelines.md).
4. **Gerador de Capas e Identidade Visual**: Entenda as diretrizes estéticas e o funcionamento do criador automático em [Modelo e Geração de Capas](docs/gerador-de-capas.md).
