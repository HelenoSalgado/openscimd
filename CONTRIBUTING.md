# 🤝 Guia de Contribuição — OpenSciMD

Seja muito bem-vindo! O **OpenSciMD** é uma iniciativa aberta e colaborativa voltada à curadoria, normalização e disponibilização de artigos científicos e livros clássicos em Markdown para o ecossistema de leitura **LeiaME**.

A colaboração de leitores, pesquisadores e revisores voluntários é essencial para mantermos o acervo com o mais alto padrão de fidelidade tipográfica e integridade textual.

Existem duas formas principais de contribuir:
1. **[Abrir uma Questão / Issue de Revisão](#-como-reportar-um-erro-ou-sugerir-revisão)** *(Ideal para leitores e voluntários sem familiaridade com Git)*
2. **[Enviar uma Alteração via Pull Request](#-contribuindo-diretamente-via-pull-request)** *(Ideal para revisores e desenvolvedores)*

---

## 🔍 Como Reportar um Erro ou Sugerir Revisão

Se você estiver lendo um livro ou artigo no **LeiaME** ou navegando pelos arquivos do repositório e encontrar:
- Erros de ortografia, pontuação ou gramática;
- Falhas de OCR remanescentes da conversão de PDFs antigos;
- Quebras de formatação, cabeçalhos incorretos ou notas de rodapé truncadas;
- Divergências com a edição-fonte original;

Você pode abrir uma **Issue** no GitHub utilizando nosso modelo oficial de revisão.

### ⚠️ Requisitos Indispensáveis para Abrir uma Questão

Para que a equipe editorial consiga localizar com precisão determinística o trecho a ser ajustado nos arquivos-fonte, **sua issue deve conter obrigatoriamente**:

1. **Título da Obra:** O nome exato do livro ou artigo (ex: *O Peregrino*, *Tratado da Oração*, etc.).
2. **Subtítulo (se houver):** Subtítulo, volume, capítulo ou número do artigo para facilitar a identificação da seção.
3. **Parágrafo Completo:** **É indispensável citar o parágrafo COMPLETO onde o erro se encontra.**  
   > 💡 *Por que o parágrafo completo é exigido?*  
   > Citar apenas uma frase isolada ou poucas palavras gera ambiguidade em textos longos. Com o parágrafo integral, as ferramentas automatizadas de busca (`grep`) localizam instantaneamente a linha exata no repositório.
4. **Sugestão de Correção:** Explique como o texto deve ficar e, se aplicável, a justificativa ou fonte de referência consultada.

👉 **[Clique aqui para abrir uma Issue de Revisão Textual](https://github.com/helenosalgado/openscimd/issues/new?template=revisao_textual.yml)**

---

## 🛠️ Contribuindo Diretamente via Pull Request

Se você deseja aplicar a correção diretamente no código-fonte em Markdown:

### 1. Diretórios das Obras
- `content/books/`: Livros e tratados finalizados.
- `content/articles/`: Artigos acadêmicos normalizados.
- `data/review/`: Obras em processo de revisão e validação preliminar.

### 2. Boas Práticas de Commit
- **Commits Atômicos por Obra:** Ao editar um livro ou artigo, faça o commit exclusivo para aquela obra. Evite misturar em um mesmo commit alterações de livros diferentes ou scripts do repositório. Isso preserva o histórico de revisões e garante que o extrator de *diffs* da API do LeiaME identifique exatamente o que mudou para notificar os leitores.
- **Mensagens Claras:** Descreva brevemente o que foi revisado (ex: `fix(editorial): correção tipográfica no cap. 4 de O Peregrino`).

### 3. Validação Local
O projeto utiliza `uv` para gestão do ambiente Python:
```bash
# Sincronizar o ambiente
uv sync

# Testar e indexar as obras locais
uv run openscimd index
```

---

## 📜 Código de Conduta e Princípios Editoriais

- **Respeito aos Originais:** As obras clássicas e históricas devem respeitar a intenção do autor original e das melhores edições de referência, evitando anacronismos ou adaptações indevidas.
- **Urbanidade:** Mantenha sempre um tom colaborativo, respeitoso e construtivo nas discussões de issues e revisões de código.

Agradecemos imensamente por dedicar seu tempo para enriquecer este acervo público e aberto!
