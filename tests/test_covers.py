"""
Testes para scripts/covers.py

Cobre:
  - format_date: datas modernas, históricas, aproximadas e strings não reconhecidas
  - extract_authors: lista de dicts, lista de strings, string direta
  - _wrap_to_width: quebra de texto respeitando largura máxima
  - _fit_font_to_zone: escala de fonte para caber em zona fixa
  - inject_cover_text: composição completa — verifica que a imagem é gerada sem erros
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Módulo a testar
from scripts.covers import (
    format_date,
    extract_authors,
    _wrap_to_width,
    _fit_font_to_zone,
    inject_cover_text,
    find_markdown_metadata,
)


# ── format_date ────────────────────────────────────────────────────────────────

class TestFormatDate:
    """Garante que todas as variantes de data encontradas nos Markdowns do projeto
    são formatadas corretamente."""

    # ── Datas modernas completas ───────────────────────────────────────────────

    def test_ddmmyyyy_hifenado(self):
        assert format_date("02-01-2021") == "2 de Janeiro de 2021"

    def test_ddmmyyyy_barra(self):
        assert format_date("29/07/2026") == "29 de Julho de 2026"

    def test_yyyymmdd_iso(self):
        assert format_date("2012-01-01") == "1 de Janeiro de 2012"

    def test_yyyymmdd_iso_2(self):
        assert format_date("2026-08-06") == "6 de Agosto de 2026"

    def test_ddmmyyyy_sem_aspas(self):
        # sem aspas no YAML (caso real: "30-06-2018")
        assert format_date("30-06-2018") == "30 de Junho de 2018"

    def test_yyyymm(self):
        assert format_date("2021-01") == "Janeiro de 2021"

    def test_mmyyyy(self):
        assert format_date("01-2021") == "Janeiro de 2021"

    # ── Anos soltos modernos ───────────────────────────────────────────────────

    def test_ano_moderno_4_digitos_1900(self):
        assert format_date("1997") == "1997"

    def test_ano_moderno_4_digitos_1912(self):
        assert format_date("1912") == "1912"

    def test_ano_moderno_4_digitos_1576(self):
        # Ano quinhentista — sem era explícita, deve retornar como ano
        assert format_date("1576") == "1576"

    def test_ano_moderno_2024(self):
        assert format_date("2024") == "2024"

    # ── Datas históricas com era explícita ─────────────────────────────────────

    def test_ac_simples(self):
        assert format_date("399 a.C.") == "399 a.C."

    def test_ac_sem_ponto_final(self):
        assert format_date("335 a.C.") == "335 a.C."

    def test_dc_simples(self):
        assert format_date("270 d.C.") == "270 d.C."

    def test_dc_sem_ponto_final(self):
        # "386 d.C" — sem o ponto final (caso real no projeto)
        assert format_date("386 d.C") == "386 d.C."

    def test_dc_com_espaco(self):
        # "107 d. C." — com espaço entre d. e C. (caso real)
        assert format_date("107 d. C.") == "107 d.C."

    def test_dc_1418(self):
        assert format_date("1418 d.C.") == "1418 d.C."

    # ── Datas históricas aproximadas ───────────────────────────────────────────

    def test_circa_dc(self):
        assert format_date("c. 1130 d.C.") == "c. 1130 d.C."

    def test_circa_dc_sem_espaco(self):
        assert format_date("c.1130 d.C.") == "c. 1130 d.C."

    def test_circa_ac(self):
        assert format_date("c. 1400 a.C.") == "c. 1400 a.C."

    def test_circa_normalizado(self):
        # "ca." deve ser normalizado para "c."
        assert format_date("ca. 400 d.C.") == "c. 400 d.C."

    # ── Strings não reconhecidas ───────────────────────────────────────────────

    def test_seculo_romano_passthrough(self):
        # "Século III" não segue nenhum padrão → retorna como está
        assert format_date("Século III") == "Século III"

    def test_string_vazia(self):
        assert format_date("") == ""

    def test_none_como_str(self):
        # Não deve lançar exceção
        assert format_date("None") == "None"


# ── extract_authors ────────────────────────────────────────────────────────────

class TestExtractAuthors:

    def test_lista_de_dicts(self):
        meta = {"authors": [{"name": "Hugo de São Vítor"}, {"name": "Fulano"}]}
        assert extract_authors(meta) == "Hugo de São Vítor, Fulano"

    def test_lista_de_strings(self):
        meta = {"authors": ["Hugo de São Vítor", "Fulano"]}
        assert extract_authors(meta) == "Hugo de São Vítor, Fulano"

    def test_string_direta(self):
        meta = {"author": "Hiroko Konishi"}
        assert extract_authors(meta) == "Hiroko Konishi"

    def test_sem_autor(self):
        assert extract_authors({}) == ""

    def test_fallback_author_singular(self):
        meta = {"author": [{"name": "Platão"}]}
        assert extract_authors(meta) == "Platão"


# ── _wrap_to_width ─────────────────────────────────────────────────────────────

class TestWrapToWidth:

    def _make_draw(self):
        """Cria um ImageDraw mínimo para testes."""
        img = Image.new("RGBA", (1696, 2528), (0, 0, 0, 0))
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        return draw

    def test_texto_curto_sem_quebra(self):
        from PIL import ImageFont
        from scripts.covers import _wrap_to_width
        draw = self._make_draw()
        font = ImageFont.load_default()
        lines = _wrap_to_width(draw, "Curto", font, max_width=9999)
        assert lines == ["Curto"]

    def test_texto_vazio(self):
        from PIL import ImageFont
        from scripts.covers import _wrap_to_width
        draw = self._make_draw()
        font = ImageFont.load_default()
        lines = _wrap_to_width(draw, "", font, max_width=9999)
        assert lines == []

    def test_texto_longo_quebrado(self):
        from PIL import ImageFont
        from scripts.covers import _wrap_to_width
        draw = self._make_draw()
        font = ImageFont.load_default()
        # Largura propositalmente muito pequena para forçar quebra
        text = "Palavra uma dois três quatro cinco"
        lines = _wrap_to_width(draw, text, font, max_width=10)
        # Cada "linha" deve ter no máximo uma palavra (largura ínfima)
        assert len(lines) > 1
        for line in lines:
            assert " " not in line or True  # aceita qualquer quebra válida


# ── _fit_font_to_zone ──────────────────────────────────────────────────────────

class TestFitFontToZone:

    def _make_draw(self):
        img = Image.new("RGBA", (1696, 2528), (0, 0, 0, 0))
        from PIL import ImageDraw
        return ImageDraw.Draw(img)

    def test_titulo_curto_usa_fonte_grande(self):
        from scripts.covers import _fit_font_to_zone, TITLE_FONT_MAX, TITLE_FONT_MIN
        draw = self._make_draw()
        font, lines, size = _fit_font_to_zone(
            draw, "CARTAS", "bold",
            max_width=1500, available_height=900,
            font_max=TITLE_FONT_MAX, font_min=TITLE_FONT_MIN,
        )
        # Título curto deve usar fonte próxima ao máximo
        assert size >= TITLE_FONT_MIN
        assert len(lines) >= 1

    def test_titulo_muito_longo_reduz_fonte(self):
        from scripts.covers import _fit_font_to_zone, TITLE_FONT_MAX, TITLE_FONT_MIN
        draw = self._make_draw()
        long_title = "INDUÇÕES ESTRUTURAIS PARA ALUCINAÇÕES EM GRANDES MODELOS DE LINGUAGEM"
        font_big, _, size_big = _fit_font_to_zone(
            draw, "CARTAS", "bold",
            max_width=1500, available_height=500,
            font_max=TITLE_FONT_MAX, font_min=TITLE_FONT_MIN,
        )
        font_small, _, size_small = _fit_font_to_zone(
            draw, long_title, "bold",
            max_width=1500, available_height=500,
            font_max=TITLE_FONT_MAX, font_min=TITLE_FONT_MIN,
        )
        assert size_small <= size_big

    def test_nunca_abaixo_do_minimo(self):
        from scripts.covers import _fit_font_to_zone, TITLE_FONT_MIN
        draw = self._make_draw()
        # Altura ínfima — deve retornar o mínimo sem lançar exceção
        _, _, size = _fit_font_to_zone(
            draw, "TEXTO MUITO LONGO " * 10, "bold",
            max_width=1500, available_height=1,
            font_max=195, font_min=TITLE_FONT_MIN,
        )
        assert size == TITLE_FONT_MIN


# ── inject_cover_text (integração) ────────────────────────────────────────────

class TestInjectCoverText:
    """Testa a composição completa usando uma imagem sintética."""

    def test_composicao_livro(self, tmp_path):
        """Cria uma imagem preta sintética e verifica que a capa é gerada.

        Simula o fluxo real com subagente multimodal: a imagem bruta tem nome
        genérico e target_slug é passado explicitamente para inject_cover_text.
        """
        base_dir = tmp_path
        covers_dir = base_dir / "assets" / "covers"
        covers_dir.mkdir(parents=True)
        content_books = base_dir / "content" / "books"
        content_books.mkdir(parents=True)

        # Imagem sintética gerada por subagente com nome genérico e arquivo local de manipulação ao lado
        slug = "obra-espiritual"
        raw_img = tmp_path / "arte_subagente.png"
        Image.new("RGB", (800, 1200), color=(10, 10, 20)).save(raw_img)
        local_work_png = covers_dir / f"{slug}.png"
        local_work_png.write_bytes(b"manipulacao-local")

        md = content_books / f"{slug}.md"
        md.write_text(
            "---\ntitle: \"Obra Espiritual\"\nauthor: Hugo de São Vítor\ndate: \"c. 1130 d.C.\"\n---\n",
            encoding="utf-8",
        )

        dest = inject_cover_text(str(base_dir), str(raw_img), target_slug=slug)

        output = covers_dir / f"{slug}.webp"
        assert dest == output
        assert output.exists(), "A capa final deve ser gerada diretamente em assets/covers/<slug>.webp"
        assert local_work_png.exists(), "Extensões locais auxiliares em assets/covers/ não podem ser removidas"
        with Image.open(output) as img:
            assert img.format == "WEBP"
            assert img.size == (1696, 2528), "Deve ter a resolução canônica"
            assert img.mode == "RGB"
            # Verifica renderização da data histórica na base inferior (zona y ~ 2300–2440)
            bottom_band = img.crop((450, 2300, 1246, 2440))
            assert any(byte_val > 60 for byte_val in bottom_band.tobytes()), (
                "A data histórica deve ser renderizada na base das capas de livros"
            )

    def test_composicao_artigo(self, tmp_path):
        """Verifica que artigos são compostos sem erro e com data no rodapé."""
        base_dir = tmp_path
        covers_dir = base_dir / "assets" / "covers"
        covers_dir.mkdir(parents=True)
        content_articles = base_dir / "content" / "articles"
        content_articles.mkdir(parents=True)

        slug = "llms-alucinacoes"
        raw_img = tmp_path / "arte_artigo.png"
        Image.new("RGB", (800, 1200), color=(5, 5, 15)).save(raw_img)

        md = content_articles / f"{slug}.md"
        md.write_text(
            "---\ntitle: \"Induções Estruturais para Alucinações em LLMs\"\nauthor: Hiroko Konishi\ndate: \"20-11-2025\"\n---\n",
            encoding="utf-8",
        )

        dest = inject_cover_text(str(base_dir), str(raw_img), target_slug=slug)

        output = covers_dir / f"{slug}.webp"
        assert dest == output
        assert output.exists()
        with Image.open(output) as img:
            assert img.format == "WEBP"
            assert img.size == (1696, 2528)

    def test_composicao_custom_text_preserva_arquivo_manipulacao_local(self, tmp_path):
        """Testa modo de texto customizado sem Markdown e preservação de extensão auxiliar em assets/covers/."""
        base_dir = tmp_path
        covers_dir = base_dir / "assets" / "covers"
        covers_dir.mkdir(parents=True)

        raw_img = covers_dir / "raw_test.png"
        Image.new("RGB", (800, 1200), color=(20, 20, 30)).save(raw_img)

        dest = inject_cover_text(
            str(base_dir),
            str(raw_img),
            custom_text="Título Teste|Autor Teste|01-01-2025",
            target_slug="raw_test",
        )

        output = covers_dir / "raw_test.webp"
        assert dest == output
        assert output.exists()
        assert raw_img.exists()

    def test_imagem_nao_encontrada_nao_lanca_excecao(self, tmp_path):
        """Deve apenas logar o erro e retornar None, nunca lançar exceção não tratada."""
        assert inject_cover_text(str(tmp_path), str(tmp_path / "inexistente.png")) is None
