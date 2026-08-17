# Diretrizes de Geração de Capas Editoriais para Agentes de IA — OpenSciMD / IRSE

Este documento orienta os agentes de IA na concepção, geração e validação de capas para artigos acadêmicos e e-books do ecossistema OpenSciMD.

---

## 1. Princípios Fundamentais de Design

- **Formato e Renderização 2D Plano**:
  - A capa deve ser sempre uma arte gráfica bidimensional plana (*flat 2D front-facing artwork*), em proporção 2:3.
  - **É terminantemente proibido** gerar mockups 3D de livros físicos, cantos dobrados, sombras de páginas projetadas, margens brancas externas ou blocos/tarjas de texto destacadas.
  - A composição deve ocupar 100% da área útil (*full-bleed canvas*).

- **Estética Editorial Nobre (*Fine-Art Chiaroscuro*)**:
  - Padrão visual clássico inspirado nas grandes editoras acadêmicas (Penguin Classics, Oxford University Press, Gallimard, Library of America).
  - Texturas nobres de pintura a óleo, contraste *chiaroscuro* dramático e paleta de cores profundas (azul-noite, carvão, obsidiana, esmeralda escuro ou bordô).

- **Simbolismo Central & Regra Teológica**:
  - Elemento conceitual centralizado, maduro e solene.
  - **Segundo Mandamento (Regra Inegociável)**: Jamais gerar figuras humanas ou representações figurativas de **Jesus Cristo**. A santidade e solenidade devem ser expressas exclusivamente por símbolos: feixes de luz celestial, livros/saltérios sagrados abertos, púlpitos austeros, arquitetura clássica/gótica sóbria ou gravuras históricas.

---

## 2. Hierarquia Tipográfica Rigorosa

Ao gerar ou renderizar o texto da capa, o agente deve seguir estritamente:

1. **Título Principal (Topo)**:
   - Tipografia serifada clássica (estilo Garamond, Baskerville, Didot).
   - Destaque maior e acabamento em tom marfim ou folha de ouro suave.
2. **Subtítulo (quando houver separação por `:` no título)**:
   - O texto após os dois pontos deve ter **corpo ligeiramente menor** e **variação tipográfica sutil** (peso mais leve ou itálico clássico).
   - **Contraste Luminoso**: Para compensar a desvantagem do corpo menor, renderize o subtítulo em **branco puro e luminoso (*bright crisp white*)**, garantindo máxima legibilidade e destaque visual sobre o fundo escuro.
3. **Nome do Autor**:
   - **Sempre em caixa baixa com iniciais maiúsculas (*Title Case*)** (ex: `Murilo Dumps`, `Plínio Sousa`, `João Calvino`), renderizado também em **branco nítido e luminoso**.
   - **Nunca** renderizar o nome do autor em caixa alta integral (*ALL CAPS*).
   - Corpo de texto menor, refinado e posicionado abaixo do título/subtítulo.
4. **Rodapé**:
   - **Para Artigos**: Data humanizada em português centralizada na base (ex: `"6 de Agosto de 2026"`).
   - **Para E-books / Livros**: A base deve permanecer limpa (sem data).

---

## 3. Estrutura Padrão de Prompt para IA

### Template para Artigos:
```text
Masterpiece fine-art editorial article cover design, full-bleed artwork occupying the entire canvas without any borders, frames, or split white boxes. Front view flat 2D graphic design only, no 3D book mockups or shadows.
Aesthetic: High-end academic publishing house (Oxford University Press, Cambridge, Gallimard).
Style: Moody chiaroscuro classical oil painting texture with rich dark [COR: midnight navy / obsidian / charcoal / deep burgundy] tones.
Visuals: [SÍMBOLO CONCEITUAL SOLENE: ex: A sacred beam of ethereal golden light illuminating an open ancient leather-bound Psalter on a stone pulpit. Strictly no human depiction of Jesus Christ].
Text layout directly rendered over the canvas:
- Main Title: '[TÍTULO PRINCIPAL ANTES DOS DOIS PONTOS]' in prominent, balanced, classical editorial serif typography with subtle gold or warm ivory hue.
- Subtitle: '[SUBTÍTULO APÓS OS DOIS PONTOS]' in slightly smaller, lighter or italicized complementary serif typography.
- Author Name: '[Nome do Autor em Title Case: ex: Murilo Dumps]' in refined, understated Title Case serif lettering (first letters capitalized, not all caps).
- Bottom Footer: '[DATA HUMANIZADA: ex: 6 de Agosto de 2026]' in clean, discreet typography centered at the base.
Pure editorial sophistication, dramatic depth, mature, minimalist and respectful.
```

### Template para E-books:
```text
Masterpiece fine-art editorial book cover design, full-bleed artwork occupying the entire canvas without any borders, frames, or split white boxes. Front view flat 2D graphic design only, no 3D book mockups or shadows.
Aesthetic: High-end literary classics publisher (Penguin Classics, Library of America).
Style: Moody classical oil painting texture with rich dark textured background and subtle atmospheric chiaroscuro lighting.
Visuals: [SÍMBOLO CONCEITUAL: ex: A refined, subtle golden classical motif seamlessly embedded into the deep textured background. Strictly no human depiction of Jesus Christ].
Text layout directly rendered over the canvas:
- Main Title: '[TÍTULO PRINCIPAL DO LIVRO]' in prominent, elegant classical editorial serif typography with gold foil texture.
- Subtitle: '[SUBTÍTULO DO LIVRO (se houver)]' in slightly smaller and lighter serif typography.
- Author: '[Nome do Autor em Title Case: ex: João Calvino]' in refined, understated Title Case typography.
- Bottom: (Empty / No date).
Pure editorial sophistication, high aesthetic rigor, dignified, mature and minimalist.
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
