# Guia de Alinhamento e Segmentação de Textos

Este documento detalha os procedimentos para garantir a correspondência estrutural 1:1 e o correto funcionamento do pipeline de revisão matemática (`pipeline-review`).

---

## 1. Fontes Brutas com Múltiplos Livros/Partes em `data/raw/`

Quando o arquivo em `data/raw/` for uma obra completa (ex.: `data/raw/The Imitation of Christ.md` contendo os Livros I, II, III e IV), e a tradução em `data/review/` ou `content/books/` estiver dividida por volume (ex.: `a-imitacao-de-cristo-livro-1.md`):

1. **Nunca execute o comparador contra o arquivo bruto multi-volume completo**, pois isso causará descompasso numérico e perda de precisão.
2. **Procedimento:** Extraia o trecho correspondente da fonte original para um arquivo pareado em `data/raw/` antes da execução:
   ```bash
   # Exemplo: Criando a matriz correspondente do Livro 1
   data/raw/the-imitation-of-christ-book-1.md
   ```
3. Execute a comparação de forma simétrica:
   ```bash
   uv run openscimd pipeline-review "data/raw/the-imitation-of-christ-book-1.md" "data/review/a-imitacao-de-cristo-livro-1.md"
   ```

---

## 2. Citações Poéticas e Versos Intercalados

Em textos patrísticos, medievais e filosóficos, o autor pode citar dísticos poéticos ou versos (ex.: Ovídio, Virgílio, poetas clássicos).

### Regra de Pareamento Estrutural:
* A oração introdutória (ex.: *"Por isso diz alguém:"* ou *"Wherefore one saith,"*) deve permanecer **acoplada ao final do parágrafo antecedente**.
* O dístico poético deve ser formatado em bloco de citação `> *...*` com quebra de linha com dois espaços (`  `) no final do primeiro verso.
* O parágrafo subsequente que comenta os versos inicia logo após o bloco.

### ✅ Exemplo de Estrutura Correta (PT e EN pareados):

**Original em Inglês (EN):**
```markdown
5 - The beginning of all temptations to evil is instability of temper... outside the door as soon as he hath knocked. Wherefore one saith,

> _Check the beginnings; once thou might'st have cured,_  
> _But now 'tis past thy skill, too long hath it endured_.

For first cometh to the mind the simple suggestion, then the strong imagination...
```

**Tradução em Português (PT):**
```markdown
5 - O princípio de todas as tentações ao mal é a instabilidade de temperamento... encontrado do lado de fora da porta logo que bateu. Por isso diz alguém:

> *Corta os princípios; uma vez poderias ter curado,*  
> *Mas agora passou tua habilidade, demasiado tempo já se demorou.*

Pois primeiro vem à mente a simples sugestão, depois a forte imaginação...
```

---

## 3. Isolamento de Notas de Rodapé no Comparador

* O comparador universal (`extract_clean_text`) extrai parágrafos do corpo textual e **ignora automaticamente** as declarações de notas de rodapé no fim do documento (`[^N]: ...`).
* As âncoras no texto (`.[^1]`) são limpas pelo extrator para permitir a avaliação semântica pura.
* A correspondência de notas (1 a N) é auditada na etapa filológica, garantindo que nenhuma nota do original foi omitida ou sintetizada.
