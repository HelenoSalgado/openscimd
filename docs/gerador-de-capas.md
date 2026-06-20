# Gerador de Capas e Modelo de Design

Este documento estabelece o **Modelo de Design das Capas** dos artigos do repositório e explica o funcionamento e configuração do script automático de geração de ilustrações por Inteligência Artificial.

---

## 🎨 Modelo de Design para Capas de Artigos

Como artigos acadêmicos nativamente não possuem ilustrações de capa, estabelecemos um padrão híbrido onde a **capa final é composta por duas camadas**:

1. **Imagem de Fundo (Background)**: Uma imagem minimalista, abstrata e conceitual que represente o tema do artigo (gerada dinamicamente por IA).
2. **Camada de Texto (Texto Dinâmico)**: Informações textuais renderizadas sobre a imagem (idealmente de forma dinâmica pelo frontend para evitar serrilhado, erros de digitação permanentes e problemas de tradução).

```text
┌────────────────────────────────────────┐
│  LOGO / REPOSITÓRIO                    │ ── Nome do acervo (MD Academics)
│                                        │
│         [ IMAGEM ABSTRATA ]            │ ── Imagem limpa sem nenhum texto,
│                                        │    servindo como fundo artístico.
│   TITULO DO ARTIGO EM DESTAQUE         │ ── Título principal legível em alto contraste
│   Subtítulo / Edição                   │
│                                        │
│   Autores & DOI                        │ ── Autores e ID persistente de referência
└────────────────────────────────────────┘
```

### Diretrizes para a Imagem de Fundo (Prompt de IA)
Para garantir que as capas pareçam profissionais e sofisticadas, a imagem gerada pela IA deve seguir estas regras:
* **Estilo Visual**: Arte vetorial abstrata, 2D flat, formas geométricas limpas ou composições minimalistas conceituais.
* **Paleta de Cores**: Tons elegantes e sóbrios, adequados ao contexto científico (evitar saturação excessiva ou neon).
* **Ausência Absoluta de Texto**: A imagem **não deve conter letras, palavras, assinaturas ou caracteres**. A inserção de texto na imagem de fundo prejudica a legibilidade do título dinâmico e quebra a consistência do design.

---

## 🛠️ Como Utilizar os Geradores de Capas

Para facilitar a manutenção e garantir eficiência, o repositório trabalha com scripts independentes para a geração de imagens por IA. As chaves de configuração do arquivo `.env` são compartilhadas, mas cada script as consome de acordo com seu provedor.

### 1. Configuração do `.env`
Primeiro, crie um arquivo `.env` na raiz do projeto (copie o modelo de [.env.example](file:///home/heleno/Documentos/GitHub/md-academics/.env.example)):

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

Toda vez que uma nova imagem de capa for gerada ou alterada, lembre-se de atualizar o índice do repositório para que o link da nova imagem de capa seja devidamente computado no [index.json](file:///home/heleno/Documentos/GitHub/md-academics/index.json):

```bash
node scripts/update-index.js
```
