// OpenSciMD - Template Tipográfico Editorial para Livro Impresso (KDP Print)
// Formato Canônico Padrão KDP: 5,5" x 8,5" (139.7mm x 215.9mm) com Margens Espelhadas e Medianiz

#let setup-book(
  title: "Obra",
  author: "Autor",
  date-orig: "",
  translator: none,
  publisher: "OpenSciMD",
  year: "2026",
  license: "Domínio Público",
  categories: ("Filosofia",),
  summary: "",
  body,
) = {
  // Configuração da Página para Impressão com Margens Espelhadas (5.5" x 8.5")
  set page(
    width: 139.7mm,
    height: 215.9mm,
    margin: (
      inside: 22mm,   // Medianiz para encadernação/cola da lombada
      outside: 16mm,  // Margem externa
      top: 20mm,      // Margem superior
      bottom: 16mm,   // Margem inferior otimizada para maior aproveitamento do texto
    ),
    header: context {
      let page-num = counter(page).get().first()
      let is-h1-page = query(heading.where(level: 1)).any(h => h.location().page() == page-num)
      // Ocultar cabeçalhos nas primeiras 4 páginas pré-textuais e nas páginas de abertura de capítulo
      if page-num > 4 and not is-h1-page {
        if calc.even(page-num) {
          // Página Par (Esquerda): Número no canto externo e Nome do Autor no centro
          align(left)[
            #text(size: 8.5pt, fill: luma(80))[#page-num]
            #h(1fr)
            #text(size: 8.5pt, tracking: 0.12em, weight: "medium")[#upper(author)]
            #h(1fr)
          ]
        } else {
          // Página Ímpar (Direita): Título da Obra no centro e Número no canto externo
          align(right)[
            #h(1fr)
            #text(size: 8.5pt, style: "italic", fill: luma(60))[#title]
            #h(1fr)
            #text(size: 8.5pt, fill: luma(80))[#page-num]
          ]
        }
      }
    },
    footer: none,
  )

  // Configurações de Tipografia e Texto
  set text(
    font: ("Cormorant Garamond", "Liberation Serif", "EB Garamond", "Georgia"),
    size: 12pt,
    lang: "pt",
    region: "BR",
    hyphenate: true,
  )

  set footnote.entry(
    clearance: 2.2em,
    gap: 0.8em,
    separator: line(length: 28%, stroke: 0.4pt + rgb("#8B6B23")),
  )

  set par(
    justify: true,
    leading: 0.72em,
    first-line-indent: 0pt,
    spacing: 1.35em,
  )

  // Controle de estado para harmonia óptica entre títulos consecutivos
  let is-after-h1 = state("after-h1", false)

  // Estilização de Cabeçalhos com Proporção Visual Natural e Harmônica
  show heading: set text(font: ("Cormorant Garamond", "Liberation Serif", "EB Garamond"))

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(1.8em)
    block(below: 1.1em)[#text(size: 18pt, weight: "bold", tracking: 0.04em)[#it.body]]
    is-after-h1.update(true)
  }

  show heading.where(level: 2): it => context {
    let after-h1 = is-after-h1.get()
    is-after-h1.update(false)
    if after-h1 {
      // Subtítulo imediatamente após Título H1: transição suave e harmônica
      block(above: 1.2em, below: 1.35em)[#text(size: 13.5pt, weight: "bold")[#it.body]]
    } else {
      // Subtítulo em meio ao texto: espaçamento superior natural e respiro confortável no parágrafo abaixo
      block(above: 1.75em, below: 1.35em)[#text(size: 13.5pt, weight: "bold")[#it.body]]
    }
  }

  show heading.where(level: 3): set text(size: 11.5pt, weight: "bold", style: "italic")
  show heading.where(level: 3): set block(above: 1.5em, below: 1.25em)

  show par: it => {
    is-after-h1.update(false)
    it
  }

  // Citações em Bloco
  show quote: it => {
    v(0.6em)
    rect(
      stroke: (left: 2.5pt + rgb("#8B6B23")),
      inset: (left: 14pt, y: 4pt),
      fill: none,
      width: 100%,
    )[
      #set text(style: "italic", size: 10pt)
      #it.body
    ]
    v(0.6em)
  }

  // --- ELEMENTOS PRÉ-TEXTUAIS (CONVENÇÃO CLÁSSICA CENTRALIZADA) ---

  // Página 1: Falsa Folha de Rosto (Half-title em folha única)
  align(center + horizon)[
    #text(size: 17pt, weight: "bold", tracking: 0.1em)[#upper(title)]
  ]
  pagebreak()

  // Página 2: Verso da Falsa Folha de Rosto (Em branco)
  pagebreak()

  // Página 3: Folha de Rosto Principal Rigorosamente Centralizada (Tipografia Pura)
  align(center + horizon)[
    #text(size: 22pt, weight: "bold", tracking: 0.06em)[#upper(title)]
    
    #if date-orig != "" [
      #v(0.6em)
      #text(size: 10.5pt, style: "italic", fill: rgb("#4A5568"))[Composição canônica: #date-orig]
    ]

    #v(3.2em)

    #text(size: 14pt, weight: "bold", tracking: 0.1em)[#upper(author)]

    #if translator != none [
      #v(0.8em)
      #text(size: 10.5pt, style: "italic", fill: rgb("#2D3748"))[Traduzido por #translator]
    ]
  ]
  pagebreak()

  // Página 4: Registro Editorial Objetivo e Não-Redundante (Alinhamento Start)
  align(center + horizon)[
    #rect(
      stroke: 0.5pt + rgb("#8B6B23"),
      inset: (x: 18pt, y: 16pt),
      radius: 2pt,
      width: 84%,
    )[
      #set text(size: 8.5pt, fill: rgb("#1A202C"))
      #set par(justify: false, leading: 0.7em)
      
      #align(left)[
        #text(weight: "bold", size: 9pt, tracking: 0.08em)[REGISTRO EDITORIAL]
        #v(0.7em)
        *Título:* #title \
        *Autor:* #author #if date-orig != "" [(#date-orig)] \
        #if translator != none [*Tradução:* #translator \ ]
        *Edição:* Edição independente, #year \
        *Extensão:* #context [ #counter(page).final().first() páginas · 5,5 × 8,5 pol. (14 × 21,6 cm) ] \
        *Assunto:* #if type(categories) == array { categories.join(", ") } else { str(categories) } \
        #if license != "" and license != none [*Licença:* #license]
      ]
    ]
  ]
  pagebreak()

  // --- CORPO DA OBRA (NUMERAÇÃO CONTÍNUA ACADÊMICA) ---
  body
}
