# Design System de Capas para Artigos Acadêmicos — OpenSciMD

Este documento define a especificação canônica, o grid tipográfico, a paleta institucional por periódico e as regras geométricas para todas as capas de **Artigos Científicos e Acadêmicos** (`content/articles/`) do ecossistema OpenSciMD / LeiaME.

> [!NOTE]
> **Preservação dos Livros e E-books**: As obras clássicas e e-books (`content/books/`) seguem a tradição visual histórica autônoma estabelecida em [`.agents/editorial/design-system-capas-livros.md`](design-system-capas-livros.md). Este *Design System* aplica-se estritamente aos artigos de periódicos.

---

## 1. Princípios Estruturais e Geometria

- **Austeridade Intelectual e Atemporalidade**:
  - As capas de artigos não utilizam ilustrações realistas, figuras humanas ou naturezas-mortas isoladas (penas, livros abertos em perspectiva, pergaminhos enrolados).
  - A identidade é puramente **geométrica-minimalista clássica**, unindo a nobreza de linhas vetoriais douradas à precisão de formas circulares translúcidas.
  - Zero risco de anacronismo ou alucinação figurativa de IA.
- **Formato e Canvas**:
  - Proporção: **2:3** vertical.
  - Resolução canônica de trabalho: `1696 × 2528 px` (ou matriz `848 × 1264 px`).
  - Renderização 100% *full-bleed* plana (2D *flat graphic design*), sem margens brancas ou molduras externas.
- **Fundo**:
  - Preto carvão / antracite profundo texturizado (`#111418` a `#15181D`), com granulação sutil e nobre de papel linho ou tela editorial pura.

---

## 2. Grid Tipográfico e Zonas Verticais

| Zona Vertical | Altura Relativa | Elementos Contidos | Tipografia e Cor |
| :--- | :---: | :--- | :--- |
| **Terço Superior** | `5% – 30%` | • Título Principal<br/>• Subtítulo<br/>• Autor(es) | • Título: Caixa Alta (ALL CAPS), serifa clássica monumental em Ouro Fosco (`#D4AF37`)<br/>• Subtítulo: *Title Case*, serifa refinada em Marfim Suave (`#F5F5F0`)<br/>• Autor: *Title Case* em Branco Marfim (`#FFFFFF`) |
| **Centro Visual** | `33% – 82%` | • Emblema Geométrico Conceitual | • Linhas douradas finas de precisão vetorial<br/>• Formas circulares e arcos com transparência suave na paleta da revista |
| **Zona Intermediária de Respiro** | `82% – 90%` | • Espaço negativo livre | • Área arejada separando a ilustração do rodapé |
| **Linha de Rodapé** | `~91% – 93%` | • `Nome da Revista • Ano` | • Serifa clássica discreta em tom ardósia/marfim suave (`#A0AEC0` / `#E2E8F0`) |
| **Margem Inferior Obrigatória** | **`Últimos 7% – 9%`** | **Espaço Vazio de Segurança** | **Proibido posicionar texto colado à borda inferior** |

> [!IMPORTANT]
> **Regra do Respiro Inferior Obrigatório (*Bottom Margin Clearance*)**:
> O rodapé (`Nome da Revista • Ano`) deve ter **no mínimo 8% da altura total do canvas de espaço livre abaixo de si** (aprox. `90 a 115 px` em `848×1264 px`, ou `180 a 230 px` em `1696×2528 px`). É expressamente proibido colar o rodapé no limite inferior da capa.

---

## 3. Paletas Institucionais por Periódico

Cada revista acadêmica do acervo possui uma assinatura cromática fixa para as formas geométricas translúcidas de fundo:

| Periódico | Área Temática | Paleta de Acento Institucional | Cores Hexadecimais |
| :--- | :--- | :--- | :--- |
| **Fides Reformata** | Teologia Reformada, Hermenêutica, Crítica Textual | Azul-Petróleo Profundo, Verde-Esmeralda e Ouro Fosco | `#0D3B4C`, `#134E3F`, `#8C733E` |
| **Peitho / Examina Antiqua** | Filosofia Antiga, Estudos Clássicos Greco-Latinos | Terracota Grega, Terra de Siena Queimada e Azul-Ardósia | `#8C3827`, `#59281E`, `#1C2630` |
| **IPDA** | Retórica, Comunicação e Teoria do Discurso | Bordeaux / Borgonha Profundo, Vinho Escuro e Bronze Pátina | `#4A121A`, `#2E0B12`, `#7A5C28` |
| **History of Science & Matemática** | História da Ciência e Educação Matemática | Azul-Cobalto Escuro, Verde-Oliva Acadêmico e Bronze Pátina | `#1A2E40`, `#3B4A2D`, `#736345` |
| **Hispania Sacra** | História da Igreja e Política Religiosa | Púrpura Imperial / Carmesim Antigo e Âmbar Queimado | `#4D1024`, `#663C1B` |
| **Revistas de Educação** | História da Educação, Políticas Educacionais | Azul Real Profundo e Cobre Ocre | `#12284C`, `#6B4423` |
| **Artigos Avulsos / IA & Computação** | Epistemologia de LLMs, Lógica Formal | Índigo Elétrico Escuro e Grafite Neutro | `#141E38`, `#242933` |

---

## 4. Pipeline de Saídas Responsivas (WebP)

Para cada capa homologada em `assets/covers/originals/<slug>.jpg`:
1. **Desktop**: `assets/covers/desktop/<slug>.webp` (`1696 × 2528 px`)
2. **Tablet**: `assets/covers/tablet/<slug>.webp` (`1200 × 1789 px`)
3. **Mobile**: `assets/covers/mobile/<slug>.webp` (`1080 × 1610 px`)
