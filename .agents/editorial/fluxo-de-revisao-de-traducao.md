# Manual e Fluxo de Revisão de Tradução (Agente Revisor)

Este documento descreve o protocolo obrigatório para o Agente de IA ou Editor Humano encarregado de garantir a fidelidade semântica de materiais traduzidos para o português no ecossistema OpenSciMD.

## O Problema das Alucinações
Os LLMs (Modelos de Linguagem Grandes) tendem a "amaciar", parafrasear e, frequentemente, alucinar textos. Em obras clássicas, teológicas e filosóficas, isso destrói a integridade da obra original. Para mitigar isso, utilizamos uma técnica de **Back-Translation** ancorada num motor matemático determinístico (MarianMT local, CPU-only).

---

## O Ciclo de Vida da Revisão

### Passo 1: Aquisição e Tradução Inicial
- **Original:** O arquivo bruto no idioma estrangeiro (ex: Inglês) fica obrigatoriamente na pasta `data/raw/` (ex: `data/raw/Apology of Socrates.md`).
- **Rascunho:** A tradução automática primária cai em `data/draft/`.
- Caso queira que a própria CLI faça a tradução crua inicial mantendo a estrutura do documento original:
  ```bash
  uv run openscimd translate-file "data/raw/arquivo.md" "data/draft/arquivo-pt.md"
  ```

### Passo 2: O Despacho para Revisão
- Mova o texto traduzido de `data/draft/` para `data/review/` (ex: `data/review/apologia-de-socrates.md`). 
- Aqui inicia-se a revisão pesada.

### Passo 3: Geração do Relatório Matemático (Pipeline Review)
- Para avaliar a fidelidade do que foi traduzido até o momento, dispare o comparador universal.
- Este comando limpa todos os metadados e formatações de ambos os arquivos para garantir uma comparação simétrica do conteúdo cru.
  ```bash
  uv run openscimd pipeline-review "data/raw/Apology of Socrates.md" "data/review/apologia-de-socrates.md"
  ```
  *(Dica: use `--limit 10` no final do comando para testar apenas os primeiros 10 blocos/parágrafos).*

### Passo 4: Leitura e Correção
- O passo anterior gerará automaticamente um arquivo de saída no mesmo local e com o mesmo nome do seu arquivo de revisão, acrescido de `-revisao.md` (ex: `data/review/apologia-de-socrates-revisao.md`).
- **O que o Agente Revisor deve fazer:**
  1. Abrir o relatório `*-revisao.md`.
  2. Procurar por blocos que acionaram o status `⚠️ Paráfrase ou Omissão` (< 70% similaridade) ou `❌ Alerta Crítico` (< 50% similaridade).
  3. Ir até o arquivo principal em `data/review/` e re-traduzir **manualmente** aquele parágrafo específico, aproximando-o estruturalmente da semântica exata original.
  4. Salvar as alterações.

### Passo 5: Aprovação Final
Após sanar os alertas do relatório, o arquivo final pode receber polimento tipográfico e gramatical e então ser movido para `data/ready/`.

---

## Como Funciona o Motor de Extração Universal
O motor Python lê os Markdown e:
- Remove o bloco YAML.
- Transforma marcações inline (`**C:V**`) em quebras de linha para parear com parágrafos tradicionais.
- Retira números sequenciais ou sobrescritos de Bíblia (`1.`, `¹`).
- Descarta linhas em branco e marcadores Markdown (links, negritos).
- Envia a "linha limpa e pura" em português para o motor MarianMT traduzir de volta pro Inglês, comparando esse retorno textualmente com a linha limpa original do autor.
