# 🌐 Fontes de Dados e Repositórios Externos

Este documento cataloga fontes de dados abertos, bibliotecas digitais e repositórios externos autorizados para consulta, ingestão de textos e enriquecimento de metadados no acervo do **OpenSciMD**.

---

## 1. Biblioteca Digital de Literatura de Países Lusófonos (UFSC / NuPILL / LAPESD)

Plataforma mantida pelo Núcleo de Pesquisa em Informática, Literatura e Linguística (NuPILL) e pelo Laboratório de Pesquisa em Sistemas Distribuídos (LAPESD) da Universidade Federal de Santa Catarina (UFSC). Disponibiliza textos integrais e dados bibliográficos conectados (*Linked Open Data* — LOD).

* **Portal Principal da Biblioteca:** [https://www.literaturabrasileira.ufsc.br/](https://www.literaturabrasileira.ufsc.br/)
* **Portal de Dados Abertos Conectados (LOD):** [https://dados.literaturabrasileira.ufsc.br/](https://dados.literaturabrasileira.ufsc.br/)
* **Endpoint SPARQL Oficial:**
  ```text
  https://dados.literaturabrasileira.ufsc.br/sparql
  ```
* **Navegação Web e Recursos:**
  * URIs canônicas de entidades (ex.: `https://dados.literaturabrasileira.ufsc.br/resource/Machado_de_Assis`).
  * Visualização gráfica em grafo através da integração com o *LodLive*.
* **Escopo e Licenciamento:**
  * Obras literárias canônicas em língua portuguesa cuja esmagadora maioria encontra-se em **Domínio Público** (autores com mais de 70 anos de falecimento).
  * Ideal para ingestão na coleção [`content/books/`](../content/books/) sob a categoria canônica `Literatura` ou `Poesia`.
  * **Critério de Ingestão:** Verificar previamente se o autor e a obra específica encontram-se em domínio público ou sob licença aberta comprovada.

---

## 2. Portal Domínio Público (MEC / Governo Federal)

Ambiente virtual do Ministério da Educação do Brasil voltado à promoção do amplo acesso às obras literárias, artísticas e científicas (na forma de textos, sons, imagens e vídeos) já em domínio público ou com autorização expressa dos titulares de direitos autorais.

* **Portal Oficial:** [https://www.dominiopublico.gov.br/](https://www.dominiopublico.gov.br/)
* **Consulta ao Acervo Literário (Exemplo - Coleção Fernando Pessoa):**
  * [Pesquisa de Obras de Fernando Pessoa no Domínio Público](https://www.dominiopublico.gov.br/pesquisa/ResultadoPesquisaObraForm.do?first=50&skip=0&ds_titulo=&co_autor=&no_autor=Fernando%20Pessoa&co_categoria=2&pagina=1&select_action=Submit&co_midia=2&co_obra=&co_idioma=&colunaOrdenar=DS_TITULO&ordem=null)
* **Escopo e Licenciamento:**
  * Documentos e PDFs históricos livres para download e reutilização sem fins comerciais.
  * O acervo serve de base para extração tipográfica via SalopDoc (`uv run openscimd import-pdf`) e catalogação em [`content/books/`](../content/books/) ou [`content/articles/`](../content/articles/).

---

## 3. Aristotle / Classical Texts (John H. Boyer)

Repositório de textos e comentários clássicos da tradição aristotélica e filosófica.

* **Endereço:** [https://aristotle.johnhboyer.com/](https://aristotle.johnhboyer.com/)
* **Escopo:** Textos clássicos, aparato crítico e estudos lógicos/ontológicos da antiguidade e período medieval.
