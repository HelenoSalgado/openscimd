# Diretório `data/review/` (Mesa Única de Edição Ativa)

**Finalidade:** Única pasta editável durante tradução, saneamento editorial e conferência linha a linha — tanto para **novas obras** vindas de `data/draft/` quanto para **obras já publicadas em `content/` que entram em re-revisão**.

## Fluxo Obrigatório
1. **Abrir revisão:** `uv run openscimd start-review <origem> [...]` (gera `<obra>.md` + manifesto `<obra>.audit.md`).
2. **Editar e auditar:** Confira em blocos de 150–200 linhas contra `data/raw/` marcando o `.audit.md` (`.agents/03-line-by-line-review.md`).
3. **Validar:** `uv run openscimd validate --file "data/review/.../<obra>.md" [--source "data/raw/<orig>"]` (deve fechar com **0 erros**).
4. **Promover:** Após aprovação humana, `uv run openscimd promote "data/review/.../<obra>.md" --index` publica em `content/` e remove a cópia ativa e o `.audit.md` desta pasta.
