# Gerador de Capas e Modelo de Design

Este documento estabelece o **Modelo de Design das Capas** dos artigos do repositório e explica o funcionamento e configuração do script automático de geração de ilustrações por Inteligência Artificial.

---

## 🎨 Modelo de Design para Capas (Coleção OpenSciMD)

Para que o repositório mantenha a estética e a credibilidade de coleções acadêmicas clássicas (como as da Oxford ou Penguin), a **capa final é gerada via pipeline automático**, combinando duas camadas processadas via código:

1. **Imagem de Fundo (Background Art)**: Uma ilustração minimalista, abstrata e conceitual que represente o tema do artigo. Gerada por IA, ela serve apenas como o "respiro visual".
2. **Camada Tipográfica e Grid Editorial**: Uma camada gerada automaticamente via `scripts` (utilizando `sharp` ou HTML/SVG) que lê os metadados do artigo (título, autor, data) e os injeta (faz "bake") na imagem final.

Isso garante que toda a coleção siga o mesmo alinhamento de texto, tipografia (fontes acadêmicas como Garamond ou Inter) e hierarquia visual, eliminando as alucinações tipográficas da IA.

```text
┌────────────────────────────────────────┐
│  OPENSCIMD COLLECTION                  │ ── Título da Coleção (Fixo)
│                                        │
│   TITULO DO ARTIGO EM DESTAQUE         │ ── Injetado pelo Script (Tipografia Uniforme)
│   Subtítulo do artigo                  │
│                                        │
│         [ IMAGEM ABSTRATA ]            │ ── Arte de fundo gerada (Centro Limpo)
│                                        │    
│   Autores                              │ ── Injetado pelo Script (Rodapé)
│   Data de Publicação                   │
└────────────────────────────────────────┘
```

### Diretrizes para a Imagem de Fundo (Prompt de IA)
Para garantir que o script de injeção de texto tenha espaço de contraste, a imagem gerada pela IA deve focar em ser a **base** da capa:
* **Estilo Visual**: Arte abstrata, 2D flat, formas limpas. A arte principal deve ocupar o centro da imagem.
* **Espaço Negativo (Respiro)**: O topo e o rodapé da imagem devem ter tons escuros ou limpos para que a tipografia branca/dourada tenha contraste perfeito.
* **Ausência Inicial de Texto (Negative Prompt)**: A imagem original bruta **NÃO PODE CONTER TEXTO NENHUM** (nem título, nem moldura). A IA deve apenas gerar o fundo, enquanto o script cuidará do texto com perfeição.

---

## 🛠️ Como Utilizar os Geradores de Capas

Para facilitar a manutenção e garantir eficiência, o repositório trabalha com scripts independentes para a geração de imagens por IA. As chaves de configuração do arquivo `.env` são compartilhadas, mas cada script as consome de acordo com seu provedor.

### 1. Configuração do `.env`
Primeiro, crie um arquivo `.env` na raiz do projeto (copie o modelo de [.env.example](file:///home/heleno/Documentos/GitHub/openscimd/.env.example)):

```bash
cp .env.example .env
```

Abra o arquivo `.env` e preencha as variáveis correspondentes à IA que você vai utilizar.

---

### 🟢 Opção A: Gerador Google Gemini (Recomendado & Nativo)
Este script utiliza o SDK oficial `@google/genai` para se comunicar diretamente com os modelos de geração de imagens do Google (como o `gemini-3.1-flash-image`).

#### Configuração do `.env` para o Gemini:
```ini
IA_KEY=sua_gemini_api_key_aqui
IA_MODEL_NAME=gemini-3.1-flash-image
```

#### Executar o comando:
```bash
# Listar os modelos de geração de imagem compatíveis:
node scripts/gemini_ai_generate_cover.js --list

# Geração padrão baseada no resumo do artigo:
node scripts/gemini_ai_generate_cover.js nome-do-artigo

# Geração com estilo personalizado opcional:
node scripts/gemini_ai_generate_cover.js nome-do-artigo "estilo pintura clássica a óleo, tons pastéis"
```

A imagem gerada será salva diretamente em `covers/nome-do-artigo.png`.

---

### ⚪ Opção B: Gerador Genérico HTTP POST (OpenAI / DALL-E)
Este script faz requisições HTTP brutas do tipo POST, compatíveis com a API do DALL-E ou proxies OpenAI-like.

#### Configuração do `.env` para DALL-E / OpenAI:
```ini
IA_KEY=seu_token_openai_aqui
IA_API_URL=https://api.openai.com/v1/images/generations
IA_MODEL_NAME=dall-e-3
```

#### Executar o comando:
```bash
node scripts/ia_generate-cover.js nome-do-artigo "estilo minimalista escandinavo"
```

A imagem gerada será salva diretamente em `covers/nome-do-artigo.webp`.

---

## 🔄 Passo Final Pós-Geração

Toda vez que uma nova imagem de capa for gerada ou alterada, lembre-se de atualizar o índice do repositório para que o link da nova imagem de capa seja devidamente computado no [index.json](file:///home/heleno/Documentos/GitHub/openscimd/index.json):

```bash
node scripts/update-index.js
```
