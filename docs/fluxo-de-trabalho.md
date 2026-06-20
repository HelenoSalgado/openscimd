# Fluxo de Trabalho e Contribuição

Este guia serve como referência rápida para o fluxo de trabalho cotidiano no repositório. Ele explica os passos necessários para incluir novos artigos científicos, mídias e como certificar-se de que a indexação funcionará corretamente.

---

## 📥 Fluxo para Adicionar Conteúdo

Para introduzir um novo artigo científico ao acervo do repositório, você deve seguir três passos principais:

### Passo 1: Escrever o artigo em Markdown
Escreva o arquivo `.md` e coloque-o na pasta `articles/`. O nome do arquivo deve ser em formato slug lowercase (ex: `reformas-filosoficas-de-petrus-ramus.md`).
No topo do arquivo, estruture o cabeçalho YAML da seguinte forma:

```yaml
---
title: "Título Completo do Artigo"
authors:
  - "Nome do Autor 1"
  - "Nome do Autor 2"
summary: "Um breve resumo ou sumário executivo do artigo."
date: 20-06-2026
categories:
  - Lógica
  - Filosofia
license: "CC BY 4.0"
UDC: "1(091):161/162"
DOI: "10.33864/2790-0037.2025.v6.i5.101-112"
---
```

> [!NOTE]
> Se houver múltiplos autores, utilize a chave `authors` (lista). Se houver apenas um autor, pode optar por usar a chave simples `author: "Nome do Autor"`. O script omitirá automaticamente a chave que não for relevante para manter o JSON final eficiente.

### Passo 2: Adicionar Imagens de Capa e o PDF Original (Opcionais)
* **Imagem de Capa**: Adicione o arquivo de imagem na pasta `covers/` com o exato mesmo nome do arquivo do artigo (ex: `covers/reformas-filosoficas-de-petrus-ramus.webp`). O script verificará o arquivo e utilizará a extensão correta.
* **PDF Original**: Adicione o arquivo `.pdf` correspondente na pasta `pdfs/` com o mesmo nome (ex: `pdfs/reformas-filosoficas-de-petrus-ramus.pdf`).

### Passo 3: Executar a Atualização do Índice
Após incluir todos os arquivos físicos, abra o seu terminal na raiz do projeto e execute:

```bash
node scripts/update-index.js
```

O script atualizará automaticamente o arquivo [index.json](index.json), calculando o tempo de leitura e inserindo a referência aos arquivos de mídia e PDF.

---

## 🧪 Como Executar os Testes

Dispomos de dois tipos de testes independentes no repositório:

### 1. Validação de Artigos e Metadados (Para Contribuintes)
Ideal para verificar se os artigos que você escreveu estão em conformidade com as regras bibliográficas e estruturais. O teste avisa sobre erros de digitação nas chaves YAML, formatação de datas, chaves mandatórias em falta ou arquivos físicos pendentes (capas e PDFs):

```bash
node scripts/test-articles.js
```

### 2. Validação da Automação (Para Desenvolvedores)
Antes de enviar qualquer modificação no script de indexação [update-index.js](scripts/update-index.js), você deve rodar os testes unitários de código para garantir que nenhuma função auxiliar foi quebrada:

```bash
node scripts/test-index.js
```

