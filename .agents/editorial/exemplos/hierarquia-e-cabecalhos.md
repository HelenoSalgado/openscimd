# Guia de Hierarquia de Cabeçalhos e Estrutura Textual

Este documento exemplifica as regras práticas de hierarquia Markdown para livros, e-books e artigos científicos no OpenSciMD.

---

## 1. Princípio do H1 Implícito no Frontmatter YAML

No ecossistema OpenSciMD e no leitor LeiaME, o título principal de nível `#` (H1) é **automaticamente extraído do metadado `title` do Frontmatter YAML**. 

Portanto, o corpo do texto Markdown **nunca deve iniciar com `#` (H1)**, pois isso duplicaria o título na renderização do leitor.

### Estrutura Canônica para Livros e Obras Divididas em Livros/Partes

```markdown
---
title: "A Imitação de Cristo: Livro I"
author: "Thomas à Kempis"
...
---

## LIVRO PRIMEIRO: ADMOESTAÇÕES PROVEITOSAS PARA A VIDA ESPIRITUAL

### CAPÍTULO I

*Da imitação de Cristo, e do desprezo do mundo e de todas as suas vaidades*

Aquele que me segue não andará em trevas, diz o Senhor.[^1] Estas são as palavras de Cristo...

2 - O seu ensinamento supera todo o ensinamento dos homens santos...
```

### Estrutura Canônica para Artigos Científicos

```markdown
---
title: "REFORMAS FILOSÓFICAS DE PETRUS RAMUS"
authors:
  - name: "Djamila Abdullazade"
...
---

## Introdução

Petrus Ramus foi uma das figuras mais controversas do Renascimento...

## 1. A Simplificação da Lógica Dialética

A reforma proposta por Ramus consistiu fundamentalmente...

### 1.1. As Três Leis do Método

A primeira lei, a lei da verdade (*lex veritatis*)...
```

---

## 2. Padrão de Níveis de Cabeçalhos (Árvore de Hierarquia)

| Nível Markdown | Função em Livros / Tratados | Função em Artigos Científicos |
| :--- | :--- | :--- |
| **`#` (H1)** | *Reservado ao YAML (`title`)* | *Reservado ao YAML (`title`)* |
| **`##` (H2)** | Nome do Livro / Parte / Seção Maior | Seções Principais (`## Introdução`, `## 1. Fundamentos`, `## Conclusão`) |
| **`###` (H3)** | Capítulos (`### CAPÍTULO I`) | Subseções (`### 1.1. O Problema da Demarcação`) |
| **`####` (H4)** | Subdivisões internas de capítulos (se houver) | Tópicos menores (`#### 1.1.1. Detalhes`) |
| **`#####` (H5)** | 🚫 **PROIBIDO para capítulos** (evitar saltos artificiais) | 🚫 **PROIBIDO para seções normais** |

---

## 3. Estilização de Cabeçalhos: Itálicos vs. Negritos

### Regra de Itálicos em Cabeçalhos (`*itálico*` ou `_itálico_`)
O uso de itálico no próprio título ou subtítulo de cabeçalho é **expressamente permitido e deve ser mantido** quando fizer parte da distinção de tratados clássicos ou temas de seções:

```markdown
## *Do Gênero*

## *Da Espécie*

### *Capítulo I: Da Doutrina*
```

### Regra de Proibição de Negrito em Cabeçalhos (`**negrito**`)
🚫 **É proibido envelopar o texto de um cabeçalho em negrito** (ex.: `## **Do Gênero**`). Títulos de nível `##` ou `###` já possuem peso visual e semântico forte nativamente no leitor LeiaME e no Markdown, tornando a marcação `**` redundante e ruidosa.

---

## 4. Formatação dos Subtítulos de Capítulos

Quando o capítulo possuir numeração formal e um título descritivo próprio:
* Opção 1 (Linha dedicada): O número do capítulo fica em **`### CAPÍTULO X`** e o subtítulo descritivo vem imediatamente abaixo, em **`*itálico*`** separado por linha em branco.
* Opção 2 (Cabeçalho estilizado direto): **`### *Capítulo I: De pensar humildemente de si mesmo*`**.

### ✅ Formas Corretas:
```markdown
### CAPÍTULO II

*De pensar humildemente de si mesmo*

Há naturalmente em todo homem um desejo de saber...
```
ou:
```markdown
### *Capítulo II: De pensar humildemente de si mesmo*

Há naturalmente em todo homem um desejo de saber...
```

### ❌ Formas Incorretas (Evitar):
```markdown
<!-- Erro 1: Negrito desnecessário em cabeçalho -->
## **Do Gênero**

<!-- Erro 2: Salto hierárquico desnecessário de H2 para H5 -->
##### CAPÍTULO II
De pensar humildemente de si mesmo
```

---

## 5. Numeração Interna de Parágrafos em Textos Clássicos

Para obras estruturadas com parágrafos numerados pelo autor ou pela tradição editorial (ex.: Tomás de Kempis, tratados renascentistas):
* O parágrafo 1 inicia normalmente com o texto (ou com a sentença inicial).
* Os parágrafos seguintes recebem a marcação `N - ` no início da linha contínua (*unwrapped*):

```markdown
Aquele que me segue não andará em trevas, diz o Senhor.[^1] Estas são as palavras de Cristo...

2 - O seu ensinamento supera todo o ensinamento dos homens santos...

3 - Que te aproveita entrar em profundas disputas acerca da Santíssima Trindade...
```

---

## 6. Paginação Crítica Clássica (Bekker, Stephanus, Busse/CAG)

Em tratados da tradição filosófica clássica e medieval dotados de paginação canônica marginal (Aristóteles/Bekker, Platão/Stephanus, Porfírio/CAG Busse):
* A notação marginal bruta (ex: `[N]`, `**[N]**`, números de páginas e linhas) deve ser padronizada na forma **`(Página. Linha)`** ou **`(Página Letra)`** antes do bloco ou inserida no fluxo da sentença.
* Exemplo canônico: `(1. 1)`, `(1. 20)`, `(2. 1)`, `(2. 5)` etc.
* Essas marcações não devem ser removidas, pois garantem a citação filológica precisa da obra.

---

## 7. Estrutura do Pós-Texto e Aparato de Notas no TOC

Para manter a renderização visual limpa e garantir a navegação precisa no Sumário (TOC) do leitor LeiaME:
1. Use um **único separador horizontal `---`** ao final do corpo do texto.
2. Agrupe as notas em subseções com cabeçalhos de nível **`###`** de acordo com sua natureza (Editoriais, do Tradutor, do Autor, Bibliográficas).

### ✅ Exemplo Canônico:
```markdown
---

### Notas Editoriais

[^1]: **Paginação Canônica**: Os números entre parênteses indicam a edição de Adolf Busse (CAG IV.1, 1887)...
[^2]: **Sobre o Tradutor**: Natanael Rinan é cristão presbiteriano e pesquisador...

### Notas do Tradutor

[^3]: O termo latino *cognatio* foi mantido para indicar a relação genealógica direta...

### Notas do Autor

[^4]: Referência às *Categorias* (1a 1 - 15b 32) de Aristóteles.
```
