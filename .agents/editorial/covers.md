# Diretrizes de Geração de Capas Editoriais para Agentes de IA — OpenSciMD / LeiaME

Este documento orienta os agentes de IA na concepção, geração e validação de capas para obras do acervo OpenSciMD, estabelecendo a distinção canônica entre **Livros** e **Artigos**.

---

## 1. Princípios Fundamentais de Design e Composição

- **Formato e Renderização 2D Plano**:
  - A capa deve ser sempre uma arte gráfica bidimensional plana (*flat 2D front-facing artwork*), em proporção **2:3** (resolução canônica `1696 × 2528 px`).
  - **É terminantemente proibido** gerar mockups 3D de livros físicos, cantos dobrados, sombras de páginas projetadas, margens brancas externas ou blocos/tarjas de texto destacados.
  - A composição deve ocupar 100% da área útil (*full-bleed canvas*), sem bordas ou molduras que cortem a imagem.

- **Correspondência Histórico-Artística (Sem Anacronismos)**:
  - Cada obra deve respeitar a **linguagem plástica, os materiais e a tradição artística da sua própria época histórica**. Nunca force um estilo de um século sobre obras de outro período:
    1. **Grécia Clássica & Helenismo (Platão, Aristóteles, Porfírio)**:
       - Escultura e relevo arquitetônico em mármore pentélico, afresco ateniense austero, baixos-relevos clássicos, colunas jônicas/dóricas, Acrópole sob luz dramática de chiaroscuro. Tons de mármore envelhecido, terracota, bronze antigo e carvão profundo.
    2. **Patrística & Idade Média (Agostinho, Inácio de Antioquia, Hugo de São Vítor, Thomas à Kempis)**:
       - Afresco românico e gótico primitivo (escola de Giotto / Fra Angelico sem representações de Cristo), textura de pergaminho cru velado, claustros monásticos solenes, luz espiritual difusa através de ogivas.
    3. **Tradição Bíblica Arcaica (Moisés / Gênesis e Êxodo)**:
       - Gravura monumental e sublime, paisagens primordiais cósmicas (águas da criação, Monte Sinai sob tempestade e nuvem de glória), rocha arcaica entalhada e luz divina dramática.
    4. **Renascimento & Humanismo (Petrus Ramus, séc. XVI)**:
       - Xilogravura renascentista e gravura em cobre (buril) no estilo de Albrecht Dürer e Hans Holbein, frontispícios de tratados humanistas quinhentistas.

- **Segundo Mandamento (Regra Teológica Inegociável)**:
  - **Jamais** gerar figuras humanas ou qualquer representação figurativa de **Jesus Cristo**. A reverência e a solenidade devem ser expressas exclusivamente por formas arquitetônicas, simbolismo intelectual puro, luz ambiente, paisagens sagradas ou alegorias conceituais.

- **Proibição Estrita de Clichês, Preguiça Criativa e Vícios de Composição**:
  - **Fim do Loop de Templos e Monumentos**: O agente de IA **NUNCA deve cair no vício repetitivo** de desenhar apenas ruínas gregas, colunas de mármore, pórticos ou claustros de pedra para qualquer obra clássica. Cada livro exige uma concepção artística própria, autêntica e dotada de personalidade singular.
  - **Proibição de Objetos Isolados (Naturezas-Mortas Artificiais)**: É expressamente proibido compor capas com objetos isolados em primeiro plano sobre pedestais, mesas ou bancadas (ex: taças soltas, cálices, pergaminhos enrolados, livros abertos sobre mesas, velas e lamparinas). Essas composições parecem catálogos de produtos e destroem o caráter monumental da arte.
  - **Exigência de Riqueza Plástica e Diversidade Visual**: O agente deve explorar a plenitude dos gêneros da pintura clássica:
    - *Pintura Histórica Vívida*: Cenas históricas reais e dramáticas com figuras humanas de época (ex: tribunais, debates, senados, congregações — respeitando sempre a proibição inegociável de representar Jesus Cristo).
    - *Paisagens Naturais e Cósmicas Sublimes*: Montanhas monumentais, desertos do Sinai, céus tempestuosos com o Verbo divino rasgando as nuvens, rios e mares primordiais.
    - *Arte Conceitual e Mística Autêntica*: Pintura de iluminação interior, relevos escultóricos complexos e xilogravuras/calcografias renascentistas densas.
  - **Proibição de Estilo Kitsch Devocional (Estética 'Adventista')**: É terminantemente proibido gerar ilustrações com aspecto de folhetos devocionais confessionais ou literatura popular kitsch (pastorais hipersaturadas, gramados verdes artificiais de conto de fadas, riachos cristalinos adocicados, pores do sol reluzentes tipo aerógrafo digital). A arte **DEVE SER OU DE ALTA ERUDIÇÃO PLÁSTICA DE MUSEU** (óleo clássico com pigmentos minerais sóbrios, chiaroscuro denso, textura tátil de linho e verniz, gravura de mestre antigo) **OU REALISMO HISTÓRICO AUSTERO E VEROSSÍMIL**. Zero adocicamento, máxima solenidade.
  - **Fidelidade ao Cerne do Texto**: A ilustração deve traduzir a tese ou o drama central da obra específica, demonstrando que o agente compreendeu o texto real e não apenas gerou um cenário decorativo genérico.

---

## 2. Hierarquia Tipográfica Rigorosa para Livros

O grid tipográfico unifica toda a coleção de livros e garante sua distinção frente aos artigos acadêmicos:

1. **Título Principal (Terço Superior)**:
   - Tipografia serifada clássica monumental (estilo Garamond, Cinzel ou Baskerville).
   - **Exclusivamente em Title Case / Caixa Alta e Baixa elegante** (ex: *Apologia de Sócrates*, *A Imitação de Cristo*, *Poética*).
   - **É TERMINANTEMENTE PROIBIDO O USO DE CAIXA ALTA TOTAL (ALL CAPS)** em títulos de livros.
   - Cor com alto contraste sobre a arte: ouro fosco nobre (*warm matte gold*), marfim luminoso (*luminous ivory*) ou branco esculpido com sombra suave.
2. **Subtítulo (quando houver)**:
   - Em corpo médio perfeitamente legível, serifado clássico ou itálico refinado, posicionado logo abaixo do título com espaçamento harmônico.
3. **Nome do Autor**:
   - **Em Title Case** (ex: `Platão`, `Aristóteles`, `Hugo de São Vítor`).
   - **Segue rigorosamente o mesmo tamanho de fonte do título principal**.
   - Espaçamento vertical generoso e confortável abaixo do título.
4. **Data Histórica Canônica (Base Inferior)**:
   - Exibição da época/data histórica da obra (ex: `399 a.C.`, `335 a.C.`, `c. 1130 d.C.`, `1576`) centralizada na base.
   - **Respiro Inferior Obrigatório**: A data deve ser posicionada com uma **margem de respiro confortável em relação à borda inferior** (~6% a 9% da altura total do canvas, ou Y a aproximadamente 2300-2350 px na resolução canônica). **Nunca deixe a data colada no limite inferior da capa**.

---

## 3. Diferenciação Entre Livros e Artigos

| Critério | Capas de Livros (`content/books/`) | Capas de Artigos (`content/articles/`) |
| :--- | :--- | :--- |
| **Estética Visual** | Arte histórica de época (afresco, mármore, iluminura, xilogravura Dürer) | Diagramas conceituais abstratos da tese acadêmica contemporânea |
| **Tipografia do Título** | Monumental clássica em **Title Case** (proibido ALL CAPS) | Serifa editorial clássica |
| **Rodapé** | Datação histórica de era (`399 a.C.`, `c. 1130 d.C.`) com respiro amplo | Data de publicação periódica contemporânea (`20 de Novembro de 2025`) ou veículo |
| **Atmosfera** | Tratado canônico e atemporal de biblioteca clássica | Periódico acadêmico universitário de pesquisa |

---

## 4. Templates de Prompt para Livros por Época Histórica

### Template A: Grécia Clássica & Filosofia Antiga (ex: Platão, Aristóteles)
```text
Masterpiece fine-art 2D book cover in vertical 2:3 aspect ratio for the classic philosophical work '[TÍTULO DA OBRA]' by [AUTOR].
Aesthetic: Authentic Ancient Greek classical heritage. Solemn Pentelic marble architectural relief, Athenian temple columns (Doric/Ionic), classical Acropolis atmosphere, rich chiaroscuro shadows with warm aged Grecian stone, terracotta, antique bronze, and charcoal textures.
100% FULL-BLEED: The artwork covers the entire canvas without borders, frames, or split boxes. Flat 2D graphic design only (NO 3D mockups, NO perspective tilt).
Typography:
- Main Title: '[Título da Obra em Title Case]' in prominent monumental classical serif in upper third with warm matte gold / luminous ivory finish and soft shadow. STRICTLY NO ALL CAPS.
- Author: '[Autor em Title Case]' in classical serif, noticeably smaller than title (50-60% size) with ample vertical breathing space.
- Bottom Date: '[DATA a.C./d.C.]' centered at the base with generous, comfortable breathing margin above the bottom edge (well-spaced from the very bottom).
Strictly NO human figures, NO open books, NO lamps, NO religious depictions.
```

### Template B: Patrística & Idade Média (ex: Agostinho, Hugo de São Vítor, Kempis)
```text
Masterpiece fine-art 2D book cover in vertical 2:3 aspect ratio for the medieval theological treatise '[TÍTULO DA OBRA]' by [AUTOR].
Aesthetic: Authentic Romanesque and early Gothic monastic heritage. Solemn cloister arches, textured aged monastic vellum, austere sacred architecture, contemplative chiaroscuro with deep midnight indigo, warm raw umber, antique burnished gold leaf, and earth tones.
100% FULL-BLEED flat 2D graphic design without borders, frames, or 3D mockups.
Typography:
- Main Title: '[Título da Obra em Title Case]' in monumental classical serif in upper third in warm antique gold or ivory with soft shadow. STRICTLY NO ALL CAPS.
- Author: '[Autor em Title Case]' in smaller refined classical serif with comfortable vertical breathing space.
- Bottom Date: '[DATA c. XXXX d.C.]' centered with generous breathing room well above the bottom border.
Strictly NO figurative depictions of Jesus Christ (Second Commandment), NO human figures, NO open books.
```

### Template C: Tradição Bíblica Arcaica (ex: Gênesis, Êxodo)
```text
Masterpiece fine-art 2D book cover in vertical 2:3 aspect ratio for the biblical text '[TÍTULO DA OBRA]' by [AUTOR].
Aesthetic: Sublime primordial and monumental sacred landscape. Primeval rocks, dramatic cosmic light piercing majestic clouds over archaic mountains, solemn chiaroscuro of creation and divine covenant. Deep obsidian, granite, sand, and radiant heavenly amber tones.
100% FULL-BLEED flat 2D graphic design without frames or borders.
Typography:
- Main Title: '[Título da Obra em Title Case]' in monumental noble serif in upper third. STRICTLY NO ALL CAPS.
- Author: '[Autor em Title Case]' noticeably smaller with ample vertical spacing.
- Bottom Date: '[DATA c. 1400 a.C.]' centered with generous breathing space above the bottom border.
Strictly NO religious figurative depictions of Christ, NO human figures, NO cliches.
```

### Template D: Renascimento & Humanismo (ex: Petrus Ramus)
```text
Masterpiece fine-art 2D book cover in vertical 2:3 aspect ratio for the Renaissance humanist treatise '[TÍTULO DA OBRA]' by [AUTOR].
Aesthetic: Renaissance woodcut and copperplate engraving in the style of Albrecht Dürer. Fine intellectual geometric diagrams, noble Renaissance architectural arches, cross-hatching textures on handmade laid paper with sepia and rich charcoal ink.
100% FULL-BLEED flat 2D graphic design without borders or 3D mockups.
Typography:
- Main Title: '[Título da Obra em Title Case]' in monumental Renaissance classical serif in upper third. STRICTLY NO ALL CAPS.
- Author: '[Autor em Title Case]' visibly smaller with ample vertical spacing.
- Bottom Date: '[DATA]' centered with generous breathing space above the bottom border.
Strictly NO human figures, NO 3D books.
```

---

## 5. Pipeline de Processamento de Arquivos

Após a aprovação manual de cada capa:
1. Salve o original em alta resolução em `assets/covers/originals/<slug>.png`.
2. Gere as versões WebP responsivas otimizadas:
   - `desktop/`: 1696 × 2528 px
   - `tablet/`: 1200 × 1789 px
   - `mobile/`: 1080 × 1610 px
3. Atualize o status na tabela do [ROADMAP_COVERS.md](file:///home/heleno/Documentos/GitHub/openscimd/ROADMAP_COVERS.md).
