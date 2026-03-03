"""Tests for internationalization."""

from ui.i18n import TRANSLATIONS, get_translator


def test_get_translator_en():
    t = get_translator("en")
    assert t("app_title") == "Ramayana Knowledge Graph"


def test_get_translator_ru():
    t = get_translator("ru")
    assert "Рамаян" in t("app_title")


def test_translator_with_kwargs():
    t = get_translator("en")
    result = t("search_sources", count=5)
    assert "5" in result


def test_translator_unknown_key():
    t = get_translator("en")
    result = t("nonexistent_key")
    assert result == "nonexistent_key"


def test_translator_fallback_to_en():
    t = get_translator("fr")  # not supported
    result = t("app_title")
    assert result == "Ramayana Knowledge Graph"  # falls back to en


def test_all_keys_have_en():
    for key, langs in TRANSLATIONS.items():
        assert "en" in langs, f"Key '{key}' missing English translation"


def test_all_keys_have_ru():
    for key, langs in TRANSLATIONS.items():
        assert "ru" in langs, f"Key '{key}' missing Russian translation"


def test_translations_not_empty():
    assert len(TRANSLATIONS) > 30
