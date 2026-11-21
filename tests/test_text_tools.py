"""Testes unitários para normalização de referências bíblicas e conversão de versículos."""

from __future__ import annotations

from pathlib import Path

from scripts.text_tools import converter_versiculos, normalize_biblical_refs


def test_normalize_biblical_refs_preserves_form_and_fixes_nonstandard(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text(
        "---\n"
        'title: "Estudo sobre João 3:16 e Rm 3, 23"\n'
        'pages: "1–10"\n'
        "---\n\n"
        "Aqui temos os 10, 20 casos, por ex. 1, 2 razões e na 3, 4 parte.\n"
        "Já padronizados: Jo 3.16, João 3.16, Hb 11.1, Hebreus 11.1, 1Co 15.3–4.\n"
        "Fora do padrão: HB 11:1, Mat. 5:3-10, 1Coríntios 10:13, I Coríntios 10:13, "
        "1 Co 10:13, I Co 10:13, joão 3:16, Salmo 61, 12 e Jo 1:1-14.\n"
        "Narrativa: A Segunda Carta aos Coríntios 2:1-3.\n\n"
        "```text\n"
        "João 8:12 e HB 11:1 em bloco de código não mudam.\n"
        "```\n",
        encoding="utf-8",
    )

    count = normalize_biblical_refs(md)
    result = md.read_text(encoding="utf-8")

    assert count == 10
    # YAML e código permanecem intactos
    assert 'title: "Estudo sobre João 3:16 e Rm 3, 23"' in result
    assert "João 8:12 e HB 11:1 em bloco de código não mudam." in result
    # Falsos positivos de prosa permanecem intactos
    assert "os 10, 20 casos" in result
    assert "por ex. 1, 2 razões" in result
    assert "na 3, 4 parte" in result
    # Formas já canônicas preservadas (extenso vs abreviado)
    assert "Jo 3.16, João 3.16, Hb 11.1, Hebreus 11.1, 1Co 15.3–4." in result
    # Formas fora do padrão corrigidas preservando extenso vs abreviado
    assert "Hb 11.1, Mt 5.3–10, 1 Coríntios 10.13, 1 Coríntios 10.13, 1Co 10.13, 1Co 10.13, João 3.16, Salmo 61.12 e Jo 1.1–14." in result
    # Forma narrativa preservada com pontuação normalizada
    assert "A Segunda Carta aos Coríntios 2.1–3." in result


def test_normalize_biblical_refs_force_abbrev_option(tmp_path: Path) -> None:
    md = tmp_path / "doc2.md"
    md.write_text("Leia João 8:12, 1 Coríntios 10:13 e Ex 20:1-17.", encoding="utf-8")

    count = normalize_biblical_refs(md, force_abbrev=True)
    result = md.read_text(encoding="utf-8")

    assert count == 3
    assert "Jo 8.12" in result
    assert "1Co 10.13" in result
    assert "Ex 20.1–17" in result


def test_normalize_biblical_refs_chained_subverses_aliases_and_safe_false_positives(tmp_path: Path) -> None:
    md = tmp_path / "chained.md"
    md.write_text(
        "Veja (Êx 34:7), 1Cro. 16:15 e Mc.10:34.\n"
        "Cadeias: Salmos 81.3 e 92:4; Colossenses 1.13 ou 1:15.\n"
        "Lista longa: (cf. Romanos 1.11; 7:14; 15:27; 1 Coríntios 2.13–15; 10:3–4; 12:1).\n"
        "Com versículos soltos: Romanos 8.29, 30; 9:10–24 e Mt 10.3, 22:13, 27:23 e 1Tm 3.16, 4:1,3.\n"
        "Subversículos e intercapítulos: Salmos 19:13b, Atos 24:6b-8a, Mc 2.18–3:6, 2 Timóteo 3.2 – 4.\n"
        "Não alterar: proporção de 2:1, 100:1, 1,33:1, Works, 2:31, Books, 2006, 7:540, "
        "Salmos 139.1–4, 23, 1 João 5.7–8, 99%, Mateus 1.7–8, 10, Malaquias (3:1), às 14:30, "
        "(números 2, 11, 12 e 13), (ver números 10, 17, 23), nos atos 1, 2 e 3, "
        "em Lucas 1, 10 e 20, em Lucas 1, 10, e 20 e capítulos de Mateus 1, 2, 3.\n"
        "Substantivos capitalizados são bíblicos: Números 31:15-18, Atos 2:38, Juízes 6:12 e NÚMEROS 6:24.\n",
        encoding="utf-8",
    )

    count = normalize_biblical_refs(md)
    result = md.read_text(encoding="utf-8")

    assert count == 21
    assert "Veja (Ex 34.7), 1Cr 16.15 e Mc 10.34." in result
    assert "Cadeias: Salmos 81.3 e 92.4; Colossenses 1.13 ou 1.15." in result
    assert "(cf. Romanos 1.11; 7.14; 15.27; 1 Coríntios 2.13–15; 10.3–4; 12.1)." in result
    assert "Romanos 8.29, 30; 9.10–24 e Mt 10.3, 22.13, 27.23 e 1Tm 3.16, 4.1,3." in result
    assert "Salmos 19.13b, Atos 24.6b–8a, Mc 2.18–3.6, 2 Timóteo 3.2–4." in result
    assert (
        "Não alterar: proporção de 2:1, 100:1, 1,33:1, Works, 2:31, Books, 2006, 7:540, "
        "Salmos 139.1–4, 23, 1 João 5.7–8, 99%, Mateus 1.7–8, 10, Malaquias (3:1), às 14:30, "
        "(números 2, 11, 12 e 13), (ver números 10, 17, 23), nos atos 1, 2 e 3, "
        "em Lucas 1, 10 e 20, em Lucas 1, 10, e 20 e capítulos de Mateus 1, 2, 3."
    ) in result
    assert "Substantivos capitalizados são bíblicos: Números 31.15–18, Atos 2.38, Juízes 6.12 e Números 6.24." in result


def test_converter_versiculos(tmp_path: Path) -> None:
    inp = tmp_path / "in.md"
    out = tmp_path / "out.md"
    inp.write_text("1. No princípio criou Deus.\n12. E disse Deus.\nLinha comum.\n", encoding="utf-8")

    converter_versiculos(inp, out)
    txt = out.read_text(encoding="utf-8")
    assert "¹ No princípio criou Deus." in txt
    assert "¹² E disse Deus." in txt
    assert "Linha comum." in txt
