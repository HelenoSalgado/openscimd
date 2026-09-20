# Guia de Referências Bíblicas, Tipografia e Notas

Este documento detalha o uso das ferramentas automatizadas e os padrões tipográficos exigidos para citações, âncoras e notas de rodapé no OpenSciMD.

---

## 1. Normalização Automática de Referências Bíblicas (CLI)

O ecossistema dispõe de um comando nativo determinístico para normalizar referências bíblicas baseado em uma lista de livros e expressões regulares:

```bash
uv run openscimd normalize-refs "caminho/do/arquivo.md"
```

### O que o comando faz:

* Converte referências com dois-pontos ou vírgula para **ponto canônico**:
  * `João 8:12` ➔ `João 8.12`
  * `1 Coríntios 10:13` ➔ `1 Coríntios 10.13`
  * `Romanos 1:21` ➔ `Romanos 1.21`

---

## 2. Tipografia e Aspas

* **Aspas Curvas Tipográficas:** Use exclusivamente aspas curvas (`“”` / `‘’`) no corpo do texto para citações e diálogos:
  * ✅ `“Aquele que me segue não andará em trevas...”`
  * ❌ `"Aquele que me segue não andará em trevas..."`
* **Destaques:**
  * `*itálico*`: Para termos em latim, grego, hebraico e títulos de obras (*De Imitatione Christi*, *Principiis obsta*).
  * `**negrito**`: Para conceitos centrais e definições substantivas.

---

## 3. Posicionamento de Âncoras de Notas de Rodapé

A âncora `[^N]` deve ficar **colada imediatamente após a palavra ou pontuação**, sem espaços:

* ✅ `Aquele que me segue não andará em trevas, diz o Senhor.[^1]`
* ✅ `...“se tornaram vãos em suas imaginações”.[^3]`
* ❌ `...diz o Senhor [^1].`
* ❌ `...diz o Senhor[^1].` *(evitar colocar antes do ponto quando a nota fecha a frase)*

---

## 4. Declaração de Notas no Rodapé

Todas as notas de rodapé devem ser declaradas no final do documento:
1. Precedidas por uma linha horizontal (`---`).
2. Com **uma linha em branco obrigatória entre cada nota**.
3. Notas filológicas do tradutor devem ser explicitamente identificadas com o prefixo **`Nota do Tradutor:`**.

### ✅ Exemplo Canônico de Declaração de Notas:

```markdown
---

[^1]: Cf. Jo 8.12.

[^2]: Cf. Ec 1.8.

[^3]: Cf. Rm 1.21.

[^4]: Cf. Jó 7.1 (Vulgata).

[^5]: Cf. 1Co 10.13.

[^6]: Nota do Tradutor: Preferiu-se o termo “apartado” (ao invés de “separado”) por conservar o sentido de recolhimento contemplativo mais próprio da tradição monástica medieval a que o texto pertence.

[^7]: Cf. Sl 4.4.
```
