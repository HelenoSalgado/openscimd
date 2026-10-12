# ⚖️ Diretrizes de Licenciamento e Direitos Autorais (OpenSciMD)

Este documento detalha os termos de licença, integridade de dados e propriedade intelectual aplicados ao projeto **OpenSciMD**.

O projeto **OpenSciMD** adota um **Licenciamento Estratificado (Split Licensing)** que distingue formalmente a camada da compilação e engenharia editorial dos textos científicos subjacentes.

---

## 1. Licença Geral da Compilação e Engenharia de Dados (CC BY-NC-ND 4.0)

Todo o trabalho autoral e editorial original desenvolvido por este projeto — incluindo:
* A curadoria, organização estrutural e esquemas de metadados (`datapackage.json`, `index-articles.json`, `index-books.json`);
* A adaptação, tipografia semântica e normalização dos textos em formato Markdown;
* A identidade visual, capas artísticas personalizadas (`assets/covers/`) e elementos gráficos (`assets/desktop/`);
* O código das ferramentas de automação, pipelines e indexação (`scripts/` e `main.py`);
* A documentação de arquitetura e diretrizes (`docs/`);

está licenciado sob a licença:

* **Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)**
  *(Attribution-NonCommercial-NoDerivatives 4.0 International)*  
  [Ver termos completos da licença](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.pt-br)

### O que isso significa:
* **Você tem permissão para:**
  * **Compartilhar e Redistribuir:** Baixar, copiar e distribuir a compilação e os arquivos em qualquer suporte ou formato.
* **Sob as seguintes condições obrigatórias:**
  * **Atribuição (BY):** Você deve dar o crédito apropriado ao projeto **OpenSciMD** e a seu autor (**Heleno Salgado**), fornecer um link para a licença e indicar se foram feitas alterações para fins de citação.
  * **Não Comercial (NC):** Você **não pode** utilizar este material para finalidades comerciais, monetização direta/indireta ou venda de pacotes.
  * **Sem Derivações (ND):** Se você remixar, transformar, reestruturar o esquema de dados ou criar a partir deste material, você **não pode distribuir o material modificado**. A obra deve ser preservada e oferecida em sua forma e estado íntegros originais.

---

## 2. Conteúdo Subjacente dos Artigos e Livros (Textos Científicos)

Os artigos acadêmicos, tratados e livros históricos presentes em `content/articles/`, `content/books/` e suas fontes originais em `assets/sources/` são propriedade intelectual de seus respectivos autores ou editoras científicas originais.

* **Conformidade Open Access:** Apenas são catalogados neste repositório materiais publicados sob licenças abertas de livre distribuição (como *Creative Commons CC-BY, CC-BY-NC*) ou que se encontram em *Domínio Público*.
* **Preservação de Direitos Originais:** Cada documento mantém no seu cabeçalho (YAML Frontmatter) e na entrada correspondente do índice (`index-articles.json` e `index-books.json`) a indicação expressa da licença sob a qual o autor original disponibilizou seu texto.
* **Integridade Editorial:** As adaptações para Markdown preservam a integralidade conceitual dos textos, limitando-se à estruturação semântica, acessibilidade e correção de imperfeições óbvias de OCR/tipografia digital.

> **Importante:** Pesquisadores e leitores que desejarem reutilizar ou citar o texto acadêmico individualmente continuam amparados pelas prerrogativas da licença original concedida pelo autor do artigo correspondente. No entanto, a compilação, o pacote estruturado e as capas do OpenSciMD permanecem protegidos sob a **CC BY-NC-ND 4.0**.

---

## 3. Repositório Público e Fontes Disponíveis

* **Fontes Públicas (`assets/sources/`):** Os arquivos originais (PDFs, HTMLs) já processados e normalizados pelo slug do Markdown ficam disponíveis publicamente para verificação acadêmica e download direto.
* **Pipeline de Revisão Colaborativa (`data/review/` e `data/ready/`):** O histórico do repositório mantém o rastreamento das etapas de revisão e de materiais prontos para que a comunidade possa acompanhar a qualidade editorial e propor melhorias de texto via Pull Request, sem desfigurar a estrutura oficial do catálogo.
