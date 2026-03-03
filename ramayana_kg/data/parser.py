"""Parse Griffith's Ramayana text into structured Verses."""

from __future__ import annotations

import re
from pathlib import Path

from ramayana_kg.models import Verse

# Kanda name mapping
KANDA_NAMES = {
    1: "Bala Kanda",
    2: "Ayodhya Kanda",
    3: "Aranya Kanda",
    4: "Kishkindha Kanda",
    5: "Sundara Kanda",
    6: "Yuddha Kanda",
}

# Regex patterns for Griffith's translation structure
BOOK_PATTERN = re.compile(r"^BOOK\s+(I{1,3}V?|VI?)\b", re.MULTILINE)
CANTO_PATTERN = re.compile(r"^CANTO\s+([IVXLC]+)\b", re.MULTILINE)

ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
    "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17,
    "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21, "XXII": 22,
    "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27,
    "XXVIII": 28, "XXIX": 29, "XXX": 30, "XXXI": 31, "XXXII": 32,
    "XXXIII": 33, "XXXIV": 34, "XXXV": 35, "XXXVI": 36, "XXXVII": 37,
    "XXXVIII": 38, "XXXIX": 39, "XL": 40, "XLI": 41, "XLII": 42,
    "XLIII": 43, "XLIV": 44, "XLV": 45, "XLVI": 46, "XLVII": 47,
    "XLVIII": 48, "XLIX": 49, "L": 50, "LI": 51, "LII": 52,
    "LIII": 53, "LIV": 54, "LV": 55, "LVI": 56, "LVII": 57,
    "LVIII": 58, "LIX": 59, "LX": 60, "LXI": 61, "LXII": 62,
    "LXIII": 63, "LXIV": 64, "LXV": 65, "LXVI": 66, "LXVII": 67,
    "LXVIII": 68, "LXIX": 69, "LXX": 70, "LXXI": 71, "LXXII": 72,
    "LXXIII": 73, "LXXIV": 74, "LXXV": 75, "LXXVI": 76, "LXXVII": 77,
    "LXXVIII": 78, "LXXIX": 79, "LXXX": 80, "LXXXI": 81, "LXXXII": 82,
    "LXXXIII": 83, "LXXXIV": 84, "LXXXV": 85, "LXXXVI": 86,
    "LXXXVII": 87, "LXXXVIII": 88, "LXXXIX": 89, "XC": 90,
    "XCI": 91, "XCII": 92, "XCIII": 93, "XCIV": 94, "XCV": 95,
    "XCVI": 96, "XCVII": 97, "XCVIII": 98, "XCIX": 99, "C": 100,
    "CI": 101, "CII": 102, "CIII": 103, "CIV": 104, "CV": 105,
    "CVI": 106, "CVII": 107, "CVIII": 108, "CIX": 109, "CX": 110,
    "CXI": 111, "CXII": 112, "CXIII": 113, "CXIV": 114, "CXV": 115,
    "CXVI": 116, "CXVII": 117, "CXVIII": 118, "CXIX": 119, "CXX": 120,
    "CXXI": 121, "CXXII": 122, "CXXIII": 123, "CXXIV": 124,
    "CXXV": 125, "CXXVI": 126, "CXXVII": 127, "CXXVIII": 128,
    "CXXIX": 129, "CXXX": 130, "CXXXI": 131,
}


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral string to integer."""
    return ROMAN_MAP.get(roman.strip(), 0)


def parse_text(text: str) -> list[Verse]:
    """Parse Griffith's Ramayana text into a list of Verse objects.

    Strategy: split by BOOK markers, then by CANTO markers within each book.
    Within each canto, split stanzas by blank-line boundaries.
    """
    verses: list[Verse] = []
    book_splits = BOOK_PATTERN.split(text)

    # book_splits: [preamble, "I", book1_text, "II", book2_text, ...]
    current_kanda = 0
    for i in range(1, len(book_splits), 2):
        roman_book = book_splits[i].strip()
        current_kanda = roman_to_int(roman_book)
        if current_kanda == 0 or current_kanda > 6:
            continue

        kanda_name = KANDA_NAMES.get(current_kanda, f"Book {current_kanda}")
        book_text = book_splits[i + 1] if i + 1 < len(book_splits) else ""

        canto_splits = CANTO_PATTERN.split(book_text)
        # canto_splits: [pre-canto, "I", canto1_text, "II", canto2_text, ...]
        for j in range(1, len(canto_splits), 2):
            roman_canto = canto_splits[j].strip()
            sarga_num = roman_to_int(roman_canto)
            if sarga_num == 0:
                continue

            canto_text = canto_splits[j + 1] if j + 1 < len(canto_splits) else ""
            stanzas = _split_stanzas(canto_text)

            for v_num, stanza_text in enumerate(stanzas, start=1):
                verse = Verse(
                    kanda=kanda_name,
                    kanda_num=current_kanda,
                    sarga=sarga_num,
                    verse_num=v_num,
                    text=stanza_text,
                )
                verses.append(verse)

    return verses


def _split_stanzas(canto_text: str) -> list[str]:
    """Split canto text into individual stanzas/verse groups.

    Stanzas are separated by blank lines. Filter out footnotes and
    very short fragments.
    """
    paragraphs = re.split(r"\n\s*\n", canto_text)
    stanzas = []
    for para in paragraphs:
        cleaned = para.strip()
        # Skip empty, footnotes, headers, and very short lines
        if not cleaned:
            continue
        if cleaned.startswith("[") and cleaned.endswith("]"):
            continue
        # Skip lines that are purely numbers or dashes
        if re.match(r"^[\d\s\-_]+$", cleaned):
            continue
        # Require minimum content
        if len(cleaned) < 20:
            continue
        # Normalize whitespace within stanza
        cleaned = re.sub(r"\s+", " ", cleaned)
        stanzas.append(cleaned)
    return stanzas


def parse_file(file_path: str | Path) -> list[Verse]:
    """Parse a Ramayana text file into Verses."""
    text = Path(file_path).read_text(encoding="utf-8")
    return parse_text(text)
