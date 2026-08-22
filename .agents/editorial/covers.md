# Diretrizes de Geração de Capas Editoriais para Agentes de IA — OpenSciMD / IRSE

Este documento orienta os agentes de IA na concepção, geração e validação de capas para artigos acadêmicos, tratados filosóficos, teológicos e e-books do ecossistema OpenSciMD.

---

## 1. Princípios Fundamentais de Design e Abstração Conceitual

- **Formato e Renderização 2D Plano**:
  - A capa deve ser sempre uma arte gráfica bidimensional plana (*flat 2D front-facing artwork*), em proporção 2:3.
  - **É terminantemente proibido** gerar mockups 3D de livros físicos, cantos dobrados, sombras de páginas projetadas, margens brancas externas ou blocos/tarjas de texto destacadas.
  - A composição deve ocupar 100% da área útil (*full-bleed canvas*).

- **Arte Abstrata, Conceitual e Temática (Fim dos Clichês Literais)**:
  - **Proibição de Clichês e Símbolos Literais**: É estritamente proibido recorrer a tropos repetitivos e clichês vazios, tais como: feixes de luz celestial óbvios (*beams of light*), bíblias/livros abertos sobre mesas, lamparinas a óleo, púlpitos genéricos ou colunas romanas descontextualizadas.
  - **Metafísica e Minimalismo Conceitual**: A ilustração deve traduzir a *ideia matriz* e a *tensão temática/filosófica* do texto em uma linguagem estética abstrata, nobre e madura. Inspire-se em:
    - *Geometria e metafísica clássica* (formas platônicas puras, intersecções de linhas e esferas, proporção áurea, diagramação geométrica austera).
    - *Gravuras e xilogravuras conceituais* (estilo Dürer, matrizes renascentistas/barrocas de alta densidade simbólica sem literalismo ingênuo).
    - *Pintura abstrata e expressionismo tonal refinado* (texturas ricas de óleo sobre linho cru, chiaroscuro abstrato, transições tonais profundas, minimalismo conceitual estilo Mark Rothko, Malevich ou gravuras de tratados científicos antigos).
    - *Paleta cromática profunda e erudita*: Obsidian, carvão, lápis-lazúli escuro, azul-noite, verde-terra, ocre queimado, ferrugem e toques discretos de folha de ouro envelhecida.

- **Segundo Mandamento (Regra Teológica Inegociável)**:
  - **Jamais** gerar figuras humanas ou qualquer representação figurativa de **Jesus Cristo**. A reverência e a solenidade devem ser expressas exclusivamente por formas abstratas, simbolismo intelectual puro, arquitetura geométrica, texturas nobres ou alegorias conceituais.

---

## 2. Hierarquia Tipográfica Rigorosa

Ao gerar ou renderizar o texto da capa, o agente deve seguir estritamente:

1. **Título Principal (Topo)**:
   - Tipografia serifada clássica de alto impacto (estilo Didot, Garamond, Bodoni ou Baskerville).
   - Destaque maior e acabamento em tom marfim nobre ou ouro fosco (*matte gold*).
2. **Subtítulo (quando houver separação por `:` no título)**:
   - O texto após os dois pontos deve ter **corpo menor** e **variação tipográfica sutil** (peso mais leve ou itálico clássico).
   - **Contraste Luminoso**: Renderize em **branco puro e nítido (*bright crisp white*)** logo abaixo do título principal.
3. **Nome do Autor**:
   - **Sempre em caixa baixa com iniciais maiúsculas (*Title Case*)** (ex: `Agostinho de Hipona`, `João Calvino`, `B. B. Warfield`), em branco nítido.
   - **Nunca** renderizar o nome do autor em caixa alta integral (*ALL CAPS*).
   - Posicionado de forma equilibrada abaixo do título/subtítulo.
4. **Área Inferior (Base Limpa)**:
   - **Para E-books / Livros**: A metade e a base inferior devem permanecer totalmente limpas de qualquer texto repetido ou datas.
   - **Para Artigos**: Apenas a data humanizada em português centralizada discretamente na base (ex: `"6 de Agosto de 2026"`).

---

## 3. Estrutura Padrão de Prompt para IA (Base Conceitual)

### Template para E-books e Obras Filosóficas/Teológicas:
```text
Masterpiece fine-art conceptual book cover design, full-bleed artwork occupying 100% of the canvas without borders, frames, or split white boxes. Flat 2D graphic design only, no 3D book mockups or angled shadows.
Aesthetic: High-end intellectual academic publishing house (Penguin Classics, Oxford World's Classics, Gallimard).
Style: Moody, abstract fine-art oil painting with heavy organic textures, minimalist chiaroscuro, and deep [PALETA: obsidian / charcoal / deep midnight / raw umber / burnished gold] tones.
Visuals: [CONCEITO FILOSÓFICO/TEOLÓGICO ABSTRATO ESPECÍFICO DA OBRA — EX: A geometric metaphysical abstraction of pure forms, intersecting ethereal spheres and infinite lines fading into deep textural darkness, representing pure intellect and immutable truth. No literal books, no lamps, no light beams, no human figures].
Text layout rendered exclusively in the upper third:
- Main Title: '[TÍTULO PRINCIPAL]' in prominent, elegant classical serif typography with warm matte gold finish.
- Subtitle: '[SUBTÍTULO (se houver)]' in slightly smaller, bright crisp white classical serif typography directly below.
- Author: '[Nome do Autor em Title Case]' in refined Title Case serif lettering in bright crisp white.
- Bottom area: Completely clean and empty of any text.
Pure intellectual sophistication, profound conceptual depth, mature, minimalist and non-literal.
```

### Template para Artigos Acadêmicos:
```text
Masterpiece fine-art conceptual editorial article cover design, full-bleed artwork occupying 100% of the canvas without borders, frames, or split white boxes. Flat 2D graphic design only, no 3D mockups.
Aesthetic: Prestigious academic journal / university press.
Style: Abstract textural chiaroscuro, deep minimalist composition with fine art etching or geometric engravings.
Visuals: [SÍMBOLO OU DIAGRAMA CONCEITUAL ABSTRATO LIGADO DIRETAMENTE À TESE DO ARTIGO. Sem clichês genéricos].
Text layout:
- Main Title: '[TÍTULO PRINCIPAL]' in classical editorial serif typography.
- Subtitle: '[SUBTÍTULO]' in crisp white complementary serif.
- Author Name: '[Nome do Autor em Title Case]'.
- Bottom Footer: '[DATA HUMANIZADA]' centered at the base.
Dignified, sober, conceptually precise and restrained.
```

---

## 4. Pipeline de Processamento no Repositório

Após a geração da imagem:
1. Salve o arquivo original em `assets/covers/originals/<slug-do-artigo>.png`.
2. Execute a geração das versões responsivas WebP (`mobile/`, `tablet/`, `desktop/`) via CLI:
   ```bash
   uv run openscimd build-covers
   ```
3. Atualize os índices com `uv run openscimd index` e valide a integridade com `uv run openscimd validate`.
