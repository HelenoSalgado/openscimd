# Extração Pesada de PDFs com `saloppdf` (MinerU)

Este documento define quando utilizar o extrator pesado `saloppdf` (baseado no **MinerU**) em vez do extrator padrão `uv run openscimd import-pdf` (**SalopDoc**).

---

## 1. Matriz de Decisão: `import-pdf` (`salopdoc`) vs. `saloppdf` (`MinerU`)

| Critério | `uv run openscimd import-pdf` (`salopdoc`) | `saloppdf` (MinerU) |
| :--- | :--- | :--- |
| **Tipo de PDF** | PDF digital nativo com camada de texto limpa | PDF escaneado (OCR), PDF histórico antigo ou imagem |
| **Layout** | Uma coluna ou layout simples com notas regulares | Múltiplas colunas, tabelas densas, fórmulas matemáticas ou notas complexas |
| **Velocidade / Recursos** | Rápido, CPU leve | Pesado (usa modelos OCR/layout em CPU ou GPU) |
| **Saída direta** | Grava diretamente em `data/draft/<slug>.md` | Grava artefatos em `artfacts-saloppdf/` (depois copie o `.md` para `data/draft/<slug>.md`) |

---

## 2. Comando Padrão de Execução

Execute sempre com as variáveis de ambiente abaixo para otimizar o uso de memória RAM quando não houver GPU dedicada:

```bash
MINERU_VIRTUAL_VRAM_SIZE=16 MINERU_MIN_BATCH_INFERENCE_SIZE=512 saloppdf \
  "data/raw/nome-do-arquivo.pdf" \
  artfacts-saloppdf
```

### Pós-processamento Obrigatório

1. Copie o Markdown extraído em `artfacts-saloppdf/markdown/<slug>.md` para `data/draft/<slug>.md` (nunca edite `data/draft/` nem `data/raw/`).
2. Abra a mesa de revisão ativa:
   ```bash
   uv run openscimd start-review "data/draft/<slug>.md" --type articles --dest "<revista>/vol-<N>/<slug>.md"
   ```
3. Siga o protocolo completo de conferência em blocos de 150–200 linhas ([`.agents/03-line-by-line-review.md`](../.agents/03-line-by-line-review.md)) confrontando diretamente contra o PDF original em `data/raw/`.
