"""Tests for Ramayana text parser."""

from ramayana_kg.data.parser import (
    KANDA_NAMES,
    _split_stanzas,
    parse_text,
    roman_to_int,
)


def test_roman_to_int_basic():
    assert roman_to_int("I") == 1
    assert roman_to_int("V") == 5
    assert roman_to_int("X") == 10
    assert roman_to_int("L") == 50
    assert roman_to_int("C") == 100


def test_roman_to_int_compound():
    assert roman_to_int("IV") == 4
    assert roman_to_int("IX") == 9
    assert roman_to_int("XIV") == 14
    assert roman_to_int("XLII") == 42
    assert roman_to_int("LXVI") == 66
    assert roman_to_int("XCIX") == 99
    assert roman_to_int("CXXXI") == 131


def test_roman_to_int_invalid():
    assert roman_to_int("") == 0
    assert roman_to_int("ABC") == 0


def test_kanda_names():
    assert len(KANDA_NAMES) == 6
    assert KANDA_NAMES[1] == "Bala Kanda"
    assert KANDA_NAMES[6] == "Yuddha Kanda"


def test_split_stanzas_basic():
    text = (
        "This is a first stanza with enough text to pass the filter."
        "\n\n"
        "This is a second stanza with enough text to pass the filter too."
    )
    stanzas = _split_stanzas(text)
    assert len(stanzas) == 2


def test_split_stanzas_filters_short():
    text = "Short\n\nThis is a stanza with enough text to pass the minimum filter."
    stanzas = _split_stanzas(text)
    assert len(stanzas) == 1


def test_split_stanzas_filters_brackets():
    text = "[Footnote 1]\n\nThis is a valid stanza with enough text for the filter."
    stanzas = _split_stanzas(text)
    assert len(stanzas) == 1


def test_split_stanzas_normalizes_whitespace():
    text = "This   is   a   stanza   with   extra   whitespace   and   enough   text."
    stanzas = _split_stanzas(text)
    assert "  " not in stanzas[0]


def test_parse_text_simple():
    text = """Preamble text here.

BOOK I.

Canto I.

The sage Valmiki praised the hero Rama for his great deeds.

Rama was the eldest son of King Dasaratha of Ayodhya city.

Canto II.

Vishvamitra came to the court to seek help from Rama.

BOOK II.

Canto I.

Kaikeyi asked for boons that would send Rama to the forest.
"""
    verses = parse_text(text)
    assert len(verses) > 0
    # All verses should have valid verse_ids
    for v in verses:
        assert v.verse_id.startswith("K")
        assert v.kanda_num in (1, 2)


def test_parse_text_kanda_assignment():
    text = """
BOOK I.

Canto I.

The mighty hero Rama prepared for his great journey ahead.

BOOK III.

Canto I.

In the Dandaka forest Rama encountered the demon Khara.
"""
    verses = parse_text(text)
    kandas = {v.kanda_num for v in verses}
    assert 1 in kandas
    assert 3 in kandas


def test_parse_text_empty():
    verses = parse_text("")
    assert verses == []


def test_parse_text_no_books():
    verses = parse_text("Just some random text without any structure.")
    assert verses == []


def test_verse_ids_unique():
    text = """
BOOK I.

Canto I.

First verse here with enough characters to pass the minimum length.

Second verse here with enough characters to also pass the length.

Canto II.

Another verse in the second canto with sufficient text content.
"""
    verses = parse_text(text)
    ids = [v.verse_id for v in verses]
    assert len(ids) == len(set(ids))


def test_parse_preserves_kanda_name():
    text = """
BOOK IV.

Canto I.

The monkeys gathered at Kishkindha mountain ready for battle.
"""
    verses = parse_text(text)
    if verses:
        assert verses[0].kanda == "Kishkindha Kanda"
        assert verses[0].kanda_num == 4
