# Arquitetura de Consumo e Integração: Leitor LeiaME

O **LeiaME** é o leitor oficial multiplataforma (Android, Desktop, iOS) construído em Kotlin Multiplatform (KMP) e Compose Multiplatform para renderização dos artigos, livros clássicos e periódicos do acervo **OpenSciMD**.

Este documento detalha como o leitor descobre, indexa e resolve os arquivos-fonte originais disponibilizados pelo OpenSciMD.

---

## 1. Localização e Extração de Slug

Quando o leitor processa uma obra contida em `content/books/` ou `content/articles/`, ele extrai o identificador único (*slug*) a partir da URL remota do arquivo Markdown:

```kotlin
fun extractSlug(remoteUrl: String): String? {
    val cleanUrl = remoteUrl.substringBefore('?').substringBefore('#').trimEnd('/')
    val lastSegment = cleanUrl.substringAfterLast('/')
    if (lastSegment.isBlank()) return null
    val slug =
        if (lastSegment.endsWith(".md", ignoreCase = true)) {
            lastSegment.dropLast(MD_EXTENSION_LENGTH)
        } else {
            lastSegment
        }
    return slug.lowercase().takeIf { it.isNotBlank() }
}
```

Exemplo:
`https://.../content/books/boecio/comentario-a-isagoge-de-porfirio.md` -> slug: `comentario-a-isagoge-de-porfirio`.

---

## 2. Algoritmo de Resolução de Fontes Originais

O leitor implementa o caso de uso `ResolveOriginalSourceUseCase` através do repositório `RemoteMarkdownRepository`. A busca por fontes originais ocorre sondando as extensões candidatas em ordem de precedência:

```kotlin
private val RAW_SOURCE_EXTENSIONS = listOf("pdf", "html", "md", "txt")

private suspend fun probeCandidateUrls(
    baseDomain: String,
    slug: String,
): String? {
    for (ext in RAW_SOURCE_EXTENSIONS) {
        val candidateUrl = "$baseDomain/assets/sources/$slug.$ext"
        try {
            val response = client.head(candidateUrl)
            if (response.status.value in AppConfig.HTTP_SUCCESS_MIN..AppConfig.HTTP_SUCCESS_MAX) {
                return candidateUrl
            }
        } catch (_: Exception) {
            // Continua testando a próxima extensão
        }
    }
    return null
}
```

A primeira URL que responder com status HTTP na faixa de sucesso (`200 OK`) é adotada como a fonte original da obra e vinculada ao botão **"Ver obra original"** na tela de detalhes do documento (`DocumentDetailScreen`).

---

## 3. Obras de Fonte Única vs. Hubs de Múltiplas Fontes

### Cenário A: Fonte Única (PDF Direto)
Se o artigo ou livro traduzido provém de um único documento ou artigo científico:
* O arquivo original deve ser salvo como `assets/sources/{slug}.pdf`.
* O leitor detecta `.pdf` na primeira iteração e abre o visualizador de PDF ou o link de download direto.

### Cenário B: Hubs de Múltiplas Fontes (Página HTML Agregadora)
Muitos tratados clássicos e edições críticas reúnem:
* Manuscrito ou arquivo Word (`.docx`) da tradução vernácula.
* Diagramação ou rascunho de editoração em PDF.
* Múltiplas fontes primárias históricas (textos em latim, grego, edições quinhentistas, etc.).

**Regra Arquitetural Essencial:**
1. Como o leitor testa `.pdf` **antes** de `.html`, se existir um arquivo `assets/sources/{slug}.pdf`, o leitor abrirá diretamente esse PDF e ignorará o HTML.
2. Portanto, para obras com múltiplas fontes, o arquivo de entrada com o slug exato deve ser obrigatoriamente **`assets/sources/{slug}.html`**.
3. Eventuais arquivos PDF e DOCX da tradução devem usar sufixos descritivos (ex.: `{slug}-traducao.pdf`, `{slug}.docx`) e estar linkados dentro da página `{slug}.html`.
4. Assim, o leitor não encontra o `{slug}.pdf` e resolve com sucesso o `{slug}.html`, apresentando ao usuário a página hub com acesso completo a todas as fontes primárias e secundárias.
