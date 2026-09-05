# ROADMAP - OpenSciMD / LeiaME

Este documento visa mapear as futuras implementações e melhorias estruturais para a automação e qualidade do processo editorial do projeto.

## 1. Tratamento de Tabelas e Ilustrações

- **Problema:** A conversão atual falha frequentemente ao extrair tabelas ou imagens complexas presentes nos PDFs originais.
- **Objetivo:** Estabelecer uma política no `.agents/` sobre como lidar com gráficos e criar ferramentas (ou integrações no pipeline) que possibilitem a recriação correta de tabelas Markdown e a extração automática/gerenciamento de assets de imagens (`![Título](assets/img/...)`).

## 2. Caça-Ruídos de OCR Sistemático e Validação Avançada

- **Problema:** O texto convertido às vezes apresenta hifenização dura de fim de linha (ex: `pala- vra`), ligaduras tipográficas (ex: `ﬁ`, `ﬂ`) e outros resquícios comuns de OCR.
- **Objetivo:** Implementar dentro do CLI (`clean-md` ou `validate`) uma rotina de varredura com dicionário de Regex padrão para identificar e remover hifenização indesejada, substituir aspas retas por aspas curvas e normalizar caracteres ligados, garantindo um texto mais limpo logo após a extração.

## 3. Dicionário Centralizado de Termos Técnicos

- **Problema:** É difícil garantir a aplicação consistente de itálico em palavras latinas, gregas ou hebraicas muito utilizadas no projeto (ex: *Ecclesia reformata*, *pneumatikois*).
- **Objetivo:** Desenvolver um catálogo unificado de termos (ex: `assets/glossary.json`) e uma função no CLI para varrer o rascunho de forma automática e aplicar a marcação de itálico (`*termo*`) corretamente onde ele não for identificado. Isso servirá também como base de conhecimento contínua para os agentes de IA.

## 4. Estimação de Qualidade de Tradução (Quality Estimation - QE)

- **Problema:** Ausência de controle matemático sobre a fidelidade das traduções feitas por LLMs.
- **Objetivo:** Integrar modelos de QE (como o COMET-QE da Unbabel) rodando localmente (via Hugging Face/PyTorch) para gerar um *score* de fidelidade (0 a 1) para cada parágrafo convertido que possua um idioma fonte. Trechos com nota baixa devem ser automaticamente marcados para revisão humana.

## 5. Tradução Reversa (Back-Translation)

- **Problema:** Modelos tendem a alucinar ou "amaciá-los" teologicamente.
- **Objetivo:** Utilizar modelos locais ultraleves (ex: MarianMT ou modelos de 1B a 3B via Ollama) para retraduzir o texto do português (já na pasta `data/review/`) de volta para o idioma original. O sistema cruzará os textos para encontrar divergências gritantes e acusá-las.

## 6. Fluxo de Revisão Multi-Agentes em Background (Antigravity CLI / agy)

- **Problema:** Poluição de contexto na IA principal e lentidão no processo síncrono.
- **Objetivo:** Ao mover um texto validado bruto de `data/draft/` para `data/review/`, a IA principal fará o trabalho de formatação, enquanto despacha um subagente em background (`invoke_subagent`). Este subagente (com um prompt de "Crítico Literário Severo") rodará com um modelo mais leve/econômico, analisando a integridade da tradução. A IA principal aguardará os alertas assíncronos do subagente para consolidar as edições finais antes de liberar para `data/ready/`.

---
*Nota: A padronização de versículos bíblicos (com array fixo) e o auto-enriquecimento do DOI já foram incorporados à codebase.*
