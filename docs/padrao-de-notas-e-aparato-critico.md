# Padrão de Notas de Rodapé e Aparato Crítico — OpenSciMD

Este documento estabelece o **padrão canônico para a estruturação de notas de rodapé, notas do tradutor e notas editoriais** em livros, e-books e artigos científicos do ecossistema **OpenSciMD** e leitor **LeiaME**.

---

## 1. O Problema da Colisão de Identificadores

Em traduções e edições críticas de artigos acadêmicos ou obras clássicas, o autor original frequentemente já possui seu próprio aparato de notas numeradas (`[^1]`, `[^2]`, ..., `[^N]`). 

Quando o tradutor ou o editor necessita incluir notas explicativas, glosas conceituais ou dados bibliográficos adicionais, **a renumeração contínua ou arbitrária é proibida**, pois:
1. **Quebra a correspondência filológica 1:1** com o texto original e o PDF de referência.
2. **Dificulta a citação acadêmica internacional**, onde o leitor espera que a nota `[^33]` do artigo corresponda exatamente à nota 33 da publicação original.

---

## 2. Padrão de *Namespaces* e Prefixos de Âncora

No Markdown (CommonMark, GitHub Flavored Markdown e LeiaME), identificadores de notas de rodapé aceitam caracteres alfanuméricos. Para garantir total desambiguação, adota-se a seguinte convenção de prefixos:

| Categoria | Prefixo da Âncora | Exemplo no Texto | Função / Finalidade |
| :--- | :--- | :--- | :--- |
| **Notas do Autor** | Numérico puro (`[^1]`, `[^2]`, ...) | `...segundo Simplício.[^4]` | Notas originais do autor da obra/artigo (100% literais e intocadas). |
| **Notas do Tradutor** | `[^nt1]`, `[^nt2]`, ... | `...pressupostos comuns (ἀξιώματα)[^nt1]` | Glosas de termos em línguas originais, escolhas de tradução e esclarecimentos filológicos. |
| **Notas Editoriais** | `[^ne1]`, `[^ne2]`, ... | `## Introdução[^ne1][^ne2]` | Notas da comissão editorial, paginação canônica crítica (CAG/Bekker/Stephanus) ou mini-bio do tradutor. |

---

## 3. Estrutura do Pós-Texto e Aparato no Sumário (TOC)

Para que o leitor LeiaME renderize uma navegação limpa no Sumário (TOC):
1. Utilize **um único separador horizontal `---`** ao final do corpo do texto.
2. Agrupe as declarações das notas em seções com cabeçalhos de nível **`###`** de acordo com sua categoria.
3. Separe cada nota com uma linha em branco.

### ✅ Exemplo Canônico Completo:

```markdown
O método sugerido por Aristóteles na *Física*[^1] apoia-se em pressupostos comuns (ἀξιώματα)[^nt1].

---

### Notas Editoriais

[^ne1]: **Paginação Canônica**: As indicações marginais referem-se à edição crítica de Berlim (CAG XVI)...
[^ne2]: **Sobre a Tradução**: Versão traduzida a partir dos manuscritos e comentários tardo-antigos...

### Notas do Tradutor

[^nt1]: **N. do T.**: *ἀξιώματα* (*axíōmata*) — Axiomas; proposições fundamentais admitidas como evidentes sem necessidade de demonstração.

### Notas do Autor

[^1]: Todas as referências ao Comentário de Filopono à *Física* I.1 de Aristóteles indicam a página e a linha da Edição da Academia de Berlim (CAG XVI)...
[^2]: Filopono *in Phys.* 3.25–30.
```

---

## 4. Rebaixamento de Âncoras do Título e Autor

Quando a obra original contiver notas de rodapé vinculadas ao título principal ou ao nome do autor (elementos que no OpenSciMD são transferidos para o Frontmatter YAML):
- **Regra**: Rebaixe as âncoras para o primeiro cabeçalho do corpo do texto Markdown (ex.: `## 1. Introdução[^1]` ou `## 1. The Opening Passage...[^1]`).
- **Proibição**: Nunca anexe âncoras dentro do Frontmatter YAML ou as espalhe arbitrariamente em palavras do primeiro parágrafo.

---

## 5. Diretrizes para Agentes de IA

Ao processar ou revisar materiais no repositório:
1. **Preserve a numeração original do autor**: Nunca altere a sequência numérica das notas do autor.
2. **Use `[^ntN]` para acréscimos de tradução**: Qualquer esclarecimento novo do tradutor deve receber o prefixo `[^nt1]`, `[^nt2]`, etc.
3. **Validação Automática**: Garanta que cada âncora no corpo tenha uma e apenas uma definição correspondente no aparato pós-texto.
