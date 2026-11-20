# 03 — Protocolo Obrigatório de Revisão Linha a Linha (Anti-Preguiça)

Revisões superficiais, amostragem do início/fim ou substituições cegas por script são a causa primária de rejeição no OpenSciMD. Todo agente executor deve seguir este protocolo auditável antes de dar qualquer revisão como concluída.

---

## 1. Papel dos Scripts vs. Auditoria Analítica

- Scripts determinísticos (`normalize-refs`, `review --check`, `validate --file`, `lint`) servem para **higiene preliminar e validação estrutural**.
- **Scripts NÃO fazem revisão textual**: quebras artificiais de página, vazamento de cabeçalhos de revista, notas multi-página partidas, omissões de orações, concordância e fidelidade semântica exigem leitura direta do arquivo revisado confrontado contra o original local (`data/raw/` ou `data/draft/`).

---

## 2. Protocolo de Leitura e Confronto em Blocos (150–200 linhas)

Nunca tente revisar um documento longo de uma só vez.

1. **Inicie via CLI**:
   ```bash
   uv run openscimd start-review <origem> [--type articles|books]
   ```
   Isso cria a cópia de trabalho em `data/review/<...>.md` e o manifesto irmão `data/review/<...>.audit.md` já fatiado em blocos de 200 linhas.
2. **Leia e edite bloco a bloco** (`L1–L200`, `L201–L400`, ...):
   - Leia o bloco inteiro do arquivo em `data/review/` com `read_file`.
   - Leia o trecho correspondente da matriz original em `data/raw/` ou `data/draft/`.
   - Verifique em cada linha do bloco:
     - Integridade integral (zero frases omitidas, truncadas ou resumidas);
     - Remoção de ruídos de OCR (`0` por `o`, hifenização partida, cabeçalhos/rodapés de página vazados, números de página soltos);
     - Parágrafos contínuos (*unwrapped*) sem quebras duras no meio de frases;
     - Regras de `.agents/01-editorial-spec.md`: cabeçalhos em Title Case sem negrito, aspas `“”`/`«»`, meia-risca `–` em intervalos numéricos, âncoras ABNT `palavra[^1].`, itálico em termos estrangeiros;
     - Notas de rodapé daquele bloco conferidas palavra por palavra contra a fonte (inclusive notas que cruzam virada de página no PDF).
3. **Atualize o manifesto `<obra>.audit.md` a cada bloco concluído**:
   - Marque `[x]` no bloco correspondente;
   - Registre o intervalo de linhas, seções/capítulos e notas conferidas (`[^1]`–`[^12]`), e um resumo objetivo das correções feitas ou `"Sem divergências"` se não houver ajustes.
4. **Separação recomendada de papéis**:
   - Em obras extensas ou traduzidas por IA, execute a auditoria final em um subagente ou sessão distinta da que produziu a tradução, exigindo a tabela completa de blocos no `.audit.md`.

---

## 3. Definition of Done (DoD) — Condição Obrigatória para Concluir

Você **só pode reportar a revisão como finalizada** quando todos os itens abaixo forem verdadeiros e verificados após a **última** edição:

1. **Cobertura 100%**: todos os blocos do arquivo `<obra>.audit.md` estão marcados como `[x]`, da linha 1 até a última linha do pós-texto de notas.
2. **Gate editorial + fonte aprovado com 0 erros**:
   ```bash
   uv run openscimd validate --file "data/review/<...>.md" --source "data/raw/<original>"
   ```
3. **Ortografia verificada**:
   ```bash
   uv run openscimd review --check "data/review/<...>.md"
   ```
   *(Zero falsos positivos ou erros reais pendentes no relatório).*
4. **Provas explícitas na resposta ao usuário**:
   - Quais blocos de linhas foram auditados (`L1–L200`, ...);
   - Contagem comparada contra a matriz (seções, notas `[^1]`..`[^N]`, notas `[^nt]`/`[^ne]`);
   - Saída literal dos comandos `validate --file` e `review --check`.

> [!IMPORTANT]
> Nunca execute `openscimd promote` sem antes apresentar o resultado da auditoria e obter autorização explícita do usuário, salvo se o usuário já tiver pedido promoção na instrução inicial.
