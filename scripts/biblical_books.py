"""Catálogo canônico de livros bíblicos e normalização preservadora (Opção B — Arábicos)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# Cada tupla:
# (abrev_canonica, extenso_canonico_padrao, variantes_extenso_validas, aliases_extenso_todos, aliases_abreviados)
_BOOK_SPECS: list[tuple[str, str, list[str], list[str], list[str]]] = [
    # Pentateuco
    ("Gn", "Gênesis", ["Gênesis"], ["Gênesis", "Genesis"], ["Gn", "Gên", "Gen"]),
    ("Ex", "Êxodo", ["Êxodo"], ["Êxodo", "Exodo"], ["Ex", "Êx", "Êxo", "Exo"]),
    ("Lv", "Levítico", ["Levítico"], ["Levítico", "Levitico"], ["Lv", "Lev"]),
    ("Nm", "Números", ["Números"], ["Números", "Numeros"], ["Nm", "Núm", "Num"]),
    ("Dt", "Deuteronômio", ["Deuteronômio"], ["Deuteronômio", "Deuteronomio"], ["Dt", "Deut", "Deu"]),
    # Históricos
    ("Js", "Josué", ["Josué"], ["Josué", "Josue"], ["Js", "Jos"]),
    ("Jz", "Juízes", ["Juízes"], ["Juízes", "Juizes"], ["Jz", "Juí", "Jui"]),
    ("Rt", "Rute", ["Rute"], ["Rute"], ["Rt", "Rut"]),
    (
        "1Sm",
        "1 Samuel",
        ["1 Samuel"],
        ["1 Samuel", "1Samuel", "I Samuel", "1º Samuel", "1ª Samuel"],
        ["1Sm", "1 Sm", "I Sm", "ISm", "1Sam", "1 Sam", "I Sam"],
    ),
    (
        "2Sm",
        "2 Samuel",
        ["2 Samuel"],
        ["2 Samuel", "2Samuel", "II Samuel", "2º Samuel", "2ª Samuel"],
        ["2Sm", "2 Sm", "II Sm", "IISm", "2Sam", "2 Sam", "II Sam"],
    ),
    (
        "1Rs",
        "1 Reis",
        ["1 Reis"],
        ["1 Reis", "1Reis", "I Reis", "1º Reis", "1ª Reis"],
        ["1Rs", "1 Rs", "I Rs", "IRs"],
    ),
    (
        "2Rs",
        "2 Reis",
        ["2 Reis"],
        ["2 Reis", "2Reis", "II Reis", "2º Reis", "2ª Reis"],
        ["2Rs", "2 Rs", "II Rs", "IIRs"],
    ),
    (
        "1Cr",
        "1 Crônicas",
        ["1 Crônicas"],
        ["1 Crônicas", "1Crônicas", "1 Cronicas", "1Cronicas", "I Crônicas", "I Cronicas", "1º Crônicas", "1ª Crônicas"],
        ["1Cr", "1 Cr", "I Cr", "ICr", "1Crôn", "1 Crôn", "1Cron", "1 Cron", "I Cron", "1Cro", "1 Cro", "I Cro", "1Crô", "1 Crô"],
    ),
    (
        "2Cr",
        "2 Crônicas",
        ["2 Crônicas"],
        ["2 Crônicas", "2Crônicas", "2 Cronicas", "2Cronicas", "II Crônicas", "II Cronicas", "2º Crônicas", "2ª Crônicas"],
        ["2Cr", "2 Cr", "II Cr", "IICr", "2Crôn", "2 Crôn", "2Cron", "2 Cron", "II Cron", "2Cro", "2 Cro", "II Cro", "2Crô", "2 Crô"],
    ),
    ("Ed", "Esdras", ["Esdras"], ["Esdras"], ["Ed", "Esd"]),
    ("Ne", "Neemias", ["Neemias"], ["Neemias"], ["Ne", "Neem", "Nee"]),
    ("Et", "Ester", ["Ester"], ["Ester"], ["Et", "Est"]),
    # Poéticos
    ("Jó", "Jó", ["Jó"], ["Jó"], ["Jó"]),
    ("Sl", "Salmos", ["Salmos", "Salmo"], ["Salmos", "Salmo"], ["Sl", "Sal", "Salm"]),
    ("Pv", "Provérbios", ["Provérbios"], ["Provérbios", "Proverbios"], ["Pv", "Prov", "Pr"]),
    ("Ec", "Eclesiastes", ["Eclesiastes"], ["Eclesiastes"], ["Ec", "Ecl"]),
    (
        "Ct",
        "Cântico dos Cânticos",
        ["Cântico dos Cânticos", "Cânticos", "Cantares"],
        ["Cântico dos Cânticos", "Cantico dos Canticos", "Cânticos", "Canticos", "Cantares"],
        ["Ct", "Cânt", "Cant"],
    ),
    # Profetas Maiores
    ("Is", "Isaías", ["Isaías"], ["Isaías", "Isaias"], ["Is", "Isa"]),
    ("Jr", "Jeremias", ["Jeremias"], ["Jeremias"], ["Jr", "Jer"]),
    ("Lm", "Lamentações", ["Lamentações"], ["Lamentações", "Lamentacoes"], ["Lm", "Lam"]),
    ("Ez", "Ezequiel", ["Ezequiel"], ["Ezequiel"], ["Ez", "Eze", "Ezeq"]),
    ("Dn", "Daniel", ["Daniel"], ["Daniel"], ["Dn", "Dan"]),
    # Profetas Menores
    ("Os", "Oseias", ["Oseias", "Oséias"], ["Oseias", "Oséias"], ["Os", "Ose", "Osé"]),
    ("Jl", "Joel", ["Joel"], ["Joel"], ["Jl", "Joe"]),
    ("Am", "Amós", ["Amós"], ["Amós", "Amos"], ["Am", "Amó", "Amo"]),
    ("Ob", "Obadias", ["Obadias"], ["Obadias"], ["Ob", "Oba"]),
    ("Jn", "Jonas", ["Jonas"], ["Jonas"], ["Jn", "Jon"]),
    ("Mq", "Miqueias", ["Miqueias", "Miquéias"], ["Miqueias", "Miquéias"], ["Mq", "Miq"]),
    ("Na", "Naum", ["Naum"], ["Naum"], ["Na", "Nau"]),
    ("Hc", "Habacuque", ["Habacuque"], ["Habacuque"], ["Hc", "Hab"]),
    ("Sf", "Sofonias", ["Sofonias"], ["Sofonias"], ["Sf", "Sof"]),
    ("Ag", "Ageu", ["Ageu"], ["Ageu"], ["Ag", "Age"]),
    ("Zc", "Zacarias", ["Zacarias"], ["Zacarias"], ["Zc", "Zac"]),
    ("Ml", "Malaquias", ["Malaquias"], ["Malaquias"], ["Ml", "Mal"]),
    # Evangelhos e Atos
    ("Mt", "Mateus", ["Mateus"], ["Mateus"], ["Mt", "Mat"]),
    ("Mc", "Marcos", ["Marcos"], ["Marcos"], ["Mc", "Mar", "Marc"]),
    ("Lc", "Lucas", ["Lucas"], ["Lucas"], ["Lc", "Luc"]),
    ("Jo", "João", ["João"], ["João", "Joao"], ["Jo", "Joã"]),
    ("At", "Atos", ["Atos dos Apóstolos", "Atos"], ["Atos dos Apóstolos", "Atos dos Apostolos", "Atos"], ["At", "Ato"]),
    # Epístolas Paulinas
    ("Rm", "Romanos", ["Romanos"], ["Romanos"], ["Rm", "Rom"]),
    (
        "1Co",
        "1 Coríntios",
        ["1 Coríntios"],
        ["1 Coríntios", "1Coríntios", "1 Corintios", "1Corintios", "I Coríntios", "I Corintios", "1º Coríntios", "1ª Coríntios"],
        ["1Co", "1 Co", "I Co", "ICo", "1Cor", "1 Cor", "I Cor"],
    ),
    (
        "2Co",
        "2 Coríntios",
        ["2 Coríntios"],
        ["2 Coríntios", "2Coríntios", "2 Corintios", "2Corintios", "II Coríntios", "II Corintios", "2º Coríntios", "2ª Coríntios"],
        ["2Co", "2 Co", "II Co", "IICo", "2Cor", "2 Cor", "II Cor"],
    ),
    ("Gl", "Gálatas", ["Gálatas"], ["Gálatas", "Galatas"], ["Gl", "Gál", "Gal"]),
    ("Ef", "Efésios", ["Efésios"], ["Efésios", "Efesios"], ["Ef", "Efé", "Efe"]),
    ("Fp", "Filipenses", ["Filipenses"], ["Filipenses"], ["Fp", "Fil", "Flp"]),
    ("Cl", "Colossenses", ["Colossenses"], ["Colossenses"], ["Cl", "Col"]),
    (
        "1Ts",
        "1 Tessalonicenses",
        ["1 Tessalonicenses"],
        ["1 Tessalonicenses", "1Tessalonicenses", "I Tessalonicenses", "1º Tessalonicenses", "1ª Tessalonicenses"],
        ["1Ts", "1 Ts", "I Ts", "ITs", "1Tes", "1 Tes", "I Tes"],
    ),
    (
        "2Ts",
        "2 Tessalonicenses",
        ["2 Tessalonicenses"],
        ["2 Tessalonicenses", "2Tessalonicenses", "II Tessalonicenses", "2º Tessalonicenses", "2ª Tessalonicenses"],
        ["2Ts", "2 Ts", "II Ts", "IITs", "2Tes", "2 Tes", "II Tes"],
    ),
    (
        "1Tm",
        "1 Timóteo",
        ["1 Timóteo"],
        ["1 Timóteo", "1Timóteo", "1 Timoteo", "1Timoteo", "I Timóteo", "I Timoteo", "1º Timóteo", "1ª Timóteo"],
        ["1Tm", "1 Tm", "I Tm", "ITm", "1Tim", "1 Tim", "I Tim"],
    ),
    (
        "2Tm",
        "2 Timóteo",
        ["2 Timóteo"],
        ["2 Timóteo", "2Timóteo", "2 Timoteo", "2Timoteo", "II Timóteo", "II Timoteo", "2º Timóteo", "2ª Timóteo"],
        ["2Tm", "2 Tm", "II Tm", "IITm", "2Tim", "2 Tim", "II Tim"],
    ),
    ("Tt", "Tito", ["Tito"], ["Tito"], ["Tt", "Tit"]),
    ("Fm", "Filemom", ["Filemom", "Filemon"], ["Filemom", "Filemon"], ["Fm", "Flm", "Filêm", "Filem"]),
    # Epístolas Gerais e Apocalipse
    ("Hb", "Hebreus", ["Hebreus"], ["Hebreus"], ["Hb", "Heb"]),
    ("Tg", "Tiago", ["Tiago"], ["Tiago"], ["Tg", "Tia", "Tgo"]),
    (
        "1Pe",
        "1 Pedro",
        ["1 Pedro"],
        ["1 Pedro", "1Pedro", "I Pedro", "1º Pedro", "1ª Pedro"],
        ["1Pe", "1 Pe", "I Pe", "IPe", "1Ped", "1 Ped", "I Ped"],
    ),
    (
        "2Pe",
        "2 Pedro",
        ["2 Pedro"],
        ["2 Pedro", "2Pedro", "II Pedro", "2º Pedro", "2ª Pedro"],
        ["2Pe", "2 Pe", "II Pe", "IIPe", "2Ped", "2 Ped", "II Ped"],
    ),
    (
        "1Jo",
        "1 João",
        ["1 João"],
        ["1 João", "1João", "1 Joao", "1Joao", "I João", "I Joao", "1º João", "1ª João"],
        ["1Jo", "1 Jo", "I Jo", "IJo", "1Joã", "1 Joã"],
    ),
    (
        "2Jo",
        "2 João",
        ["2 João"],
        ["2 João", "2João", "2 Joao", "2Joao", "II João", "II Joao", "2º João", "2ª João"],
        ["2Jo", "2 Jo", "II Jo", "IIJo", "2Joã", "2 Joã"],
    ),
    (
        "3Jo",
        "3 João",
        ["3 João"],
        ["3 João", "3João", "3 Joao", "3Joao", "III João", "III Joao", "3º João", "3ª João"],
        ["3Jo", "3 Jo", "III Jo", "IIIJo", "3Joã", "3 Joã"],
    ),
    ("Jd", "Judas", ["Judas"], ["Judas"], ["Jd", "Jud"]),
    ("Ap", "Apocalipse", ["Apocalipse"], ["Apocalipse"], ["Ap", "Apo", "Apoc"]),
]


def _alias_lookup_key(alias: str) -> str:
    cleaned = re.sub(r"\s+", " ", alias.rstrip(".").strip()).lower()
    cleaned = re.sub(r"^iii(?:\s+|(?=[a-záéíóúâêôãõç]))", "3 ", cleaned)
    cleaned = re.sub(r"^ii(?:\s+|(?=[a-záéíóúâêôãõç]))", "2 ", cleaned)
    cleaned = re.sub(r"^i(?:\s+|(?=[a-záéíóúâêôãõç]))", "1 ", cleaned)
    cleaned = re.sub(r"^(\d+)[ºª]\s*", r"\1 ", cleaned)
    return re.sub(r"\s+", "", cleaned)


def _alias_to_regex(alias: str) -> str:
    escaped = re.escape(alias)
    return escaped.replace(r"\ ", r"\s*")


BIBLE_BOOKS: list[str] = []
BIBLE_BOOK_CANONICAL_MAP: dict[str, str] = {}
_FULL_CANONICAL_MAP: dict[str, str] = {}
_VALID_CANONICAL_TOKENS: set[str] = set()

_CASE_INSENSITIVE_PATTERNS: list[str] = []
_CASE_SENSITIVE_PATTERNS: list[str] = []

for _canon_abbr, _canon_full_default, _valid_fulls, _full_aliases, _abbrev_aliases in _BOOK_SPECS:
    _VALID_CANONICAL_TOKENS.add(_canon_abbr)
    for _vf in _valid_fulls:
        _VALID_CANONICAL_TOKENS.add(_vf)

    for _fa in _full_aliases:
        _key = _alias_lookup_key(_fa)
        BIBLE_BOOKS.append(_alias_to_regex(_fa))
        BIBLE_BOOK_CANONICAL_MAP[_key] = _canon_abbr
        if _fa in _valid_fulls:
            _FULL_CANONICAL_MAP[_key] = _fa
        elif "salmo" == _key:
            _FULL_CANONICAL_MAP[_key] = "Salmo"
        elif "canticos" == _key:
            _FULL_CANONICAL_MAP[_key] = "Cânticos"
        elif "atosdosapostolos" == _key:
            _FULL_CANONICAL_MAP[_key] = "Atos dos Apóstolos"
        else:
            _FULL_CANONICAL_MAP[_key] = _canon_full_default

        # "Jó" curto (2 letras) requer J maiúsculo para evitar falsos positivos em prosa
        if len(re.sub(r"\s+", "", _fa)) <= 2:
            _CASE_SENSITIVE_PATTERNS.append(re.escape(_fa))
            _CASE_SENSITIVE_PATTERNS.append(re.escape(_fa.upper()))
        else:
            _CASE_INSENSITIVE_PATTERNS.append(_alias_to_regex(_fa))

    for _aa in _abbrev_aliases:
        _key = _alias_lookup_key(_aa)
        BIBLE_BOOKS.append(_alias_to_regex(_aa))
        BIBLE_BOOK_CANONICAL_MAP[_key] = _canon_abbr

        compact = re.sub(r"\s+", "", _aa)
        # Siglas de 2 letras puras (ex.: Hb, Mt, Os, Ex) e prefixos romanos (I Co, ICo) exigem maiúscula
        if len(compact) <= 2 or compact.startswith(("I", "II", "III")):
            _CASE_SENSITIVE_PATTERNS.append(_alias_to_regex(_aa))
            _upper_variant = _aa.upper()
            if _upper_variant != _aa:
                _CASE_SENSITIVE_PATTERNS.append(_alias_to_regex(_upper_variant))
        else:
            _CASE_INSENSITIVE_PATTERNS.append(_alias_to_regex(_aa))


def _pattern_sort_key(pat: str) -> tuple[int, str]:
    raw_len = len(pat.replace(r"\s*", " ").replace("\\", ""))
    return (raw_len, pat)


_FULL_AND_CI_SORTED = sorted(set(_CASE_INSENSITIVE_PATTERNS), key=_pattern_sort_key, reverse=True)
_CS_SORTED = sorted(set(_CASE_SENSITIVE_PATTERNS), key=_pattern_sort_key, reverse=True)


_VERSE_PART = r"\d+(?-i:[a-d]{1,2})?"

_EXTRA_VERSES_RE = re.compile(
    r"(?:[ \t]*,[ \t]*\d+(?!\d)(?-i:[a-d]{1,2})?(?![ \t]*[:.])\b"
    r"(?:[ \t]*[-–][ \t]*\d+(?!\d)(?-i:[a-d]{1,2})?(?![ \t]*[:.])\b)?)*"
)

_CHAIN_CONTINUATION_RE = re.compile(
    rf"(?:;[ \t]*|,[ \t]*|[ \t]+(?:e|ou)[ \t]+)"
    rf"(?P<ref>"
    rf"(?P<chap>\d+)[ \t]*(?P<sep>[:.])[ \t]*(?P<verse>{_VERSE_PART})"
    rf"(?:[ \t]*(?P<dash>[-–])[ \t]*(?:(?P<chap_end>\d+)[ \t]*(?P<sep_end>[:.])[ \t]*)?(?P<verse_end>{_VERSE_PART}))?"
    rf")\b"
)


@dataclass(frozen=True)
class BiblicalRefMatch:
    """Representa uma ocorrência bíblica (explícita, narrativa ou encadeada) localizada em prosa."""

    start: int
    end: int
    raw: str
    expected: str
    kind: Literal["explicit", "narrative", "chained"]

    @property
    def is_canonical(self) -> bool:
        return self.raw == self.expected


def build_biblical_book_pattern() -> str:
    """Retorna padrão regex combinando nomes longos e siglas (curtas apenas Xx ou XX)."""
    ci_alt = "|".join(_FULL_AND_CI_SORTED)
    cs_alt = "|".join(_CS_SORTED)
    return f"(?:(?i:{ci_alt})|(?-i:{cs_alt}))"


def build_biblical_reference_regex() -> re.Pattern[str]:
    """Compila regex para referências bíblicas explícitas (com subversículo e intervalo intercapítulo)."""
    book_pat = build_biblical_book_pattern()
    return re.compile(
        rf"(?<![\w])(?P<book_raw>(?P<book>{book_pat})\.?)(?:[ \t]+|(?<=\.)[ \t]*)"
        rf"(?P<chap>\d+)[ \t]*(?P<sep>[:.,])[ \t]*(?P<verse>{_VERSE_PART})"
        rf"(?:[ \t]*(?P<dash>[-–])[ \t]*(?:(?P<chap_end>\d+)[ \t]*(?P<sep_end>[:.])[ \t]*)?(?P<verse_end>{_VERSE_PART}))?\b"
    )


def build_narrative_biblical_regex() -> re.Pattern[str]:
    """Compila regex para formas narrativas livres (ex.: 'Segunda Carta aos Coríntios 2:1')."""
    return re.compile(
        r"(?i:(?:(?:Primeir[oa]|Segund[oa]|Terceir[oa])[ \t]+)?(?:Carta|Epístola|Livro|Evangelho)[ \t]+"
        r"(?:aos?|dos?|das?|de|segundo)[ \t]+[A-ZÀ-Ÿa-zà-ÿ]+(?:[ \t]+(?:de|dos?|das?|e)[ \t]+[A-ZÀ-Ÿa-zà-ÿ]+)*)"
        rf"[ \t]+(?P<chap>\d+)[ \t]*(?P<sep>[:.,])[ \t]*(?P<verse>{_VERSE_PART})"
        rf"(?:[ \t]*(?P<dash>[-–])[ \t]*(?:(?P<chap_end>\d+)[ \t]*(?P<sep_end>[:.])[ \t]*)?(?P<verse_end>{_VERSE_PART}))?\b"
    )


def _format_ref_numbers(match: re.Match[str], target_sep: str, normalize_ranges: bool) -> str:
    chap = match.group("chap")
    verse = match.group("verse")
    dash = match.group("dash")
    chap_end = match.group("chap_end")
    verse_end = match.group("verse_end")
    if dash and verse_end:
        out_dash = "–" if normalize_ranges else dash
        if chap_end:
            return f"{chap}{target_sep}{verse}{out_dash}{chap_end}{target_sep}{verse_end}"
        return f"{chap}{target_sep}{verse}{out_dash}{verse_end}"
    return f"{chap}{target_sep}{verse}"


def _overlaps_any(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(not (end <= s or start >= e) for s, e in spans)


def iter_biblical_reference_matches(
    masked_text: str,
    *,
    target_sep: str = ".",
    canonical_abbrev: bool = True,
    force_abbrev: bool = False,
    normalize_ranges: bool = True,
) -> list[BiblicalRefMatch]:
    """Localiza referências bíblicas explícitas, narrativas e encadeadas com livro implícito."""
    matches: list[BiblicalRefMatch] = []
    anchor_spans: list[tuple[int, int]] = []
    anchors: list[re.Match[str]] = []

    narrative_re = build_narrative_biblical_regex()
    for m in narrative_re.finditer(masked_text):
        span = (m.start(), m.end())
        anchor_spans.append(span)
        anchors.append(m)
        prefix = m.group(0)[: m.start("chap") - m.start()]
        numbers = _format_ref_numbers(m, target_sep=target_sep, normalize_ranges=normalize_ranges)
        matches.append(
            BiblicalRefMatch(
                start=m.start(),
                end=m.end(),
                raw=m.group(0),
                expected=f"{prefix}{numbers}",
                kind="narrative",
            )
        )

    explicit_re = build_biblical_reference_regex()
    for m in explicit_re.finditer(masked_text):
        if _overlaps_any(m.start(), m.end(), anchor_spans):
            continue
        span = (m.start(), m.end())
        anchor_spans.append(span)
        anchors.append(m)
        raw_book = m.group("book_raw")
        out_book = (
            normalize_biblical_book_token(raw_book, force_abbrev=force_abbrev)
            if canonical_abbrev
            else raw_book
        )
        numbers = _format_ref_numbers(m, target_sep=target_sep, normalize_ranges=normalize_ranges)
        matches.append(
            BiblicalRefMatch(
                start=m.start(),
                end=m.end(),
                raw=m.group(0),
                expected=f"{out_book} {numbers}",
                kind="explicit",
            )
        )

    emitted_spans = list(anchor_spans)
    for anchor in sorted(anchors, key=lambda item: item.start()):
        pos = anchor.end()
        while True:
            extra_match = _EXTRA_VERSES_RE.match(masked_text, pos)
            if extra_match:
                pos = extra_match.end()
            chain_match = _CHAIN_CONTINUATION_RE.match(masked_text, pos)
            if not chain_match:
                break
            ref_start, ref_end = chain_match.start("ref"), chain_match.end("ref")
            if _overlaps_any(ref_start, ref_end, emitted_spans):
                break
            emitted_spans.append((ref_start, ref_end))
            matches.append(
                BiblicalRefMatch(
                    start=ref_start,
                    end=ref_end,
                    raw=chain_match.group("ref"),
                    expected=_format_ref_numbers(
                        chain_match,
                        target_sep=target_sep,
                        normalize_ranges=normalize_ranges,
                    ),
                    kind="chained",
                )
            )
            pos = chain_match.end()

    matches.sort(key=lambda item: item.start)
    return matches


def resolve_canonical_book(matched_book: str) -> str:
    """Retorna a abreviação canônica brasileira de 2 letras (e arábico colado) para qualquer variante."""
    key = _alias_lookup_key(matched_book)
    return BIBLE_BOOK_CANONICAL_MAP.get(key, matched_book.rstrip(".").strip())


def normalize_biblical_book_token(raw_book_with_opt_dot: str, force_abbrev: bool = False) -> str:
    """Normaliza livro/abreviação fora do padrão preservando extenso vs abreviado (salvo force_abbrev=True)."""
    clean_raw = raw_book_with_opt_dot.rstrip(".").strip()
    key = _alias_lookup_key(clean_raw)
    if force_abbrev:
        return BIBLE_BOOK_CANONICAL_MAP.get(key, clean_raw)
    if key in _FULL_CANONICAL_MAP:
        return _FULL_CANONICAL_MAP[key]
    return BIBLE_BOOK_CANONICAL_MAP.get(key, clean_raw)


def is_canonical_biblical_book(raw_book_with_opt_dot: str) -> bool:
    """Retorna True se o nome ou sigla bíblica já está exatamente no padrão canônico (sem ponto residual)."""
    stripped = raw_book_with_opt_dot.strip()
    if stripped.endswith("."):
        return False
    return stripped in _VALID_CANONICAL_TOKENS
