# 🎓 MD Academics - Artigos Acadêmicos e Científicos

Bem-vindo ao **MD Academics**, um repositório centralizado projetado para o armazenamento, organização e compartilhamento de artigos acadêmicos e científicos estruturados em formato Markdown. 

O repositório conta com uma automação construída em Node.js que extrai metadados acadêmicos (como DOI, UDC e Licenças) e compila automaticamente o índice geral para consumo por aplicações externas.

---

## 🚀 Como Funciona a Automação?

Nosso script de indexação analisa a pasta `articles` e compila todos os metadados do cabeçalho YAML para o arquivo [index.json](index.json).

### Principais Recursos:
* **Preservação de IDs de Artigos**: O script preserva IDs de artigos pré-existentes, garantindo que referências antigas nunca sejam alteradas ou quebradas.
* **Estimação Inteligente de Leitura**: O tempo estimado de leitura é calculado baseando-se em uma velocidade média acadêmica de 200 palavras por minuto, limpando o texto de código fonte, HTML e formatação do Markdown para um valor realístico.
* **Busca Automática de Capas**: Detecta extensões de mídia comuns (`.webp`, `.png`, `.jpg`, `.jpeg`, `.svg`) na pasta de capas e vincula-as dinamicamente ao artigo.
* **Detecção de PDF Original**: Caso exista um PDF correspondente na pasta `pdfs`, uma chave de URL direta para ele (`pdf_url`) é criada de forma automática.
* **JSON Otimizado**: Chaves com valores não preenchidos (vazias, nulas ou arrays vazios) são totalmente omitidas para manter o arquivo de índice com consumo otimizado de dados.

---

## 📂 Estrutura do Repositório

* [articles/](articles/): Artigos acadêmicos escritos em Markdown.
* [covers/](covers/): Capas oficiais dos artigos em formato de imagem.
* [pdfs/](pdfs/): Versão original dos artigos em formato PDF.
* [scripts/](scripts/): Ferramentas de automação e testes automatizados.
* [docs/](docs/): Documentações detalhadas de funcionamento do repositório.

---

## 🛠️ Execução e Desenvolvimento

### 1. Atualizar o Índice Geral (`index.json`)
Sempre que novos artigos, imagens ou PDFs forem adicionados, rode o seguinte comando no terminal:
```bash
node scripts/update-index.js
```

### 2. Executar Testes de Código
Para garantir que as automações e funções auxiliares do script de indexação estejam funcionando corretamente, execute:
```bash
node scripts/test-index.js
```

### 3. Validar Artigos e Metadados (Para Contribuintes)
Para verificar a qualidade de formatação dos artigos, checar se há erros de digitação nas chaves YAML, campos obrigatórios ausentes ou se faltam imagens de capa e PDFs correspondentes, execute:
```bash
node scripts/test-articles.js
```

---

## 🤝 Como Contribuir

Toda contribuição acadêmica ou técnica é muito bem-vinda! Se você deseja submeter novos artigos ou propor melhorias nas automações, por favor consulte a nossa documentação de apoio:

1. **Entenda os Bastidores**: Leia o nosso guia de [Arquitetura e Funcionamento do Repositório](docs/arquitetura.md).
2. **Saiba como Publicar**: Siga o passo a passo em [Fluxo de Trabalho e Contribuição](docs/fluxo-de-trabalho.md).
3. **Diretrizes de Metadados**: Veja a lista de chaves YAML recomendadas para artigos científicos em [Diretrizes de Metadados Acadêmicos (MDC)](docs/metadata_guidelines.md).
