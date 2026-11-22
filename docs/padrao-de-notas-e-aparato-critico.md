# Padrão de Notas de Rodapé e Aparato Crítico — OpenSciMD

Este documento estabelece o **padrão canônico para estruturação de notas de rodapé, notas do tradutor e notas editoriais** em livros e artigos científicos do ecossistema **OpenSciMD / LeiaME**.

---

## 1. O Problema da Colisão de Identificadores

Em traduções e edições críticas, o autor original frequentemente já possui seu próprio aparato numerado (`[^1]`, `[^2]`, ..., `[^N]`). Quando o tradutor ou o editor acrescenta notas explicativas, **a renumeração arbitrária é proibida**, pois quebraria a correspondência 1:1 com a paginação e citação da obra original.

---

## 2. Padrão de *Namespaces* e Prefixos de Âncora

| Categoria | Prefixo da Âncora | Exemplo no Texto (ABNT) | Função / Finalidade |
| :--- | :--- | :--- | :--- |
| **Notas do Autor** | Numérico puro (`[^1]`, `[^2]`, ...) | `...segundo Simplício[^4].` | Notas originais do autor (100% literais e contínuas de 1 a N). |
| **Notas do Tradutor** | `[^nt1]`, `[^nt2]`, ... | `...pressupostos comuns (*axíōmata*)[^nt1].` | Glosas de termos em línguas originais e escolhas filológicas. |
| **Notas Editoriais** | `[^ne1]`, `[^ne2]`, ... | `## Introdução[^ne1][^ne2]` | Paginação canônica (CAG/Bekker/Stephanus), proveniência e mini-bio do tradutor. |

---

## 3. Posicionamento das Âncoras — Padrão ABNT/Português

Adota-se estritamente o **padrão ABNT/português**:
1. A âncora `[^id]` fica **colada imediatamente à palavra, expressão ou aspas de fechamento, ANTES do sinal de pontuação** (`palavra[^1].`, `“citação”[^nt1].`, `termo[^2],`).
2. **Proibido** espaço ou tabulação antes da âncora (`palavra [^1].`).
3. **Proibido** posicionar a âncora após o ponto ou vírgula final (`.[^1]`, `,[^1]`).
   - *Exceção única*: pontos que pertencem a abreviações canônicas no fim da sentença (`etc.[^1]`, `a.C.[^1]`, `d.C.[^1]`, `Cf.[^1]`).

---

## 4. Estrutura do Pós-Texto e Aparato no Sumário (TOC)

Para navegação limpa no Sumário (TOC) do leitor **LeiaME**:
1. Utilize **um único separador horizontal `---`** ao final do corpo do texto.
2. Agrupe as declarações em subseções `###` por categoria (`### Notas Editoriais`, `### Notas do Tradutor`, `### Notas do Autor`).
3. Separe **cada definição de nota com uma linha em branco**.
4. Mantenha sequência contínua a partir de 1 em cada namespace (`[^ne1]`, `[^ne2]`...).
5. Sob `### Notas do Tradutor`, dispensa-se o prefixo redundante `**N. do T.**:` (a subseção já identifica a autoria da nota).

### ✅ Exemplo Canônico Completo

```markdown
O método sugerido por Aristóteles na *Física*[^1] apoia-se em pressupostos comuns (*axíōmata*)[^nt1].

---

### Notas Editoriais

[^ne1]: **Paginação Canônica**: As indicações marginais referem-se à edição crítica de Berlim (CAG XVI).

[^ne2]: **Sobre o Tradutor**: Mini-biografia do tradutor primário, quando aplicável.

### Notas do Tradutor

[^nt1]: *ἀξιώματα* (*axíōmata*) — Axiomas; proposições fundamentais admitidas sem demonstração.

### Notas do Autor

[^1]: Todas as referências ao Comentário de Filopono à *Física* I.1 de Aristóteles indicam página e linha da CAG XVI.

[^2]: Filopono, *in Phys.*, 3.25–30.
```

---

## 5. Rebaixamento de Âncoras do Título e Autor

Quando a obra original contiver notas vinculadas ao título principal ou ao nome do autor (elementos migrados para o YAML):
- **Regra**: rebaixe as âncoras para o **primeiro cabeçalho do corpo** (`## Introdução[^ne1][^1]`).
- **Proibição**: nunca insira âncoras `[^...]` dentro do Frontmatter YAML.
