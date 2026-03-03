"""Internationalization (i18n) for Ramayana KG Streamlit UI."""

from __future__ import annotations

from typing import Callable

TRANSLATIONS: dict[str, dict[str, str]] = {
    "app_title": {"en": "Ramayana Knowledge Graph", "ru": "Граф Знаний Рамаяны"},
    "app_subtitle": {
        "en": "LLM Entity Extraction + Hybrid RAG (Vector + Graph)",
        "ru": "LLM Извлечение Сущностей + Гибридный RAG (Вектор + Граф)",
    },
    "language": {"en": "Language", "ru": "Язык"},

    # Tabs
    "tab_explorer": {"en": "KG Explorer", "ru": "Обзор Графа"},
    "tab_search": {"en": "Hybrid Search & Q&A", "ru": "Гибридный Поиск"},
    "tab_dashboard": {"en": "Dashboard", "ru": "Дашборд"},
    "tab_cooccurrence": {"en": "Co-occurrence", "ru": "Совместные упоминания"},
    "tab_settings": {"en": "Settings & Pipeline", "ru": "Настройки"},

    # Explorer tab
    "explorer_search": {"en": "Search entities", "ru": "Поиск сущностей"},
    "explorer_placeholder": {"en": "Enter entity name (e.g. Rama, Lanka)", "ru": "Введите имя сущности (напр. Rama, Lanka)"},
    "explorer_results": {"en": "Search Results", "ru": "Результаты поиска"},
    "explorer_profile": {"en": "Entity Profile", "ru": "Профиль сущности"},
    "explorer_relationships": {"en": "Relationships", "ru": "Связи"},
    "explorer_verses": {"en": "Mentioned in Verses", "ru": "Упоминания в стихах"},
    "explorer_family": {"en": "Family Tree", "ru": "Семейное древо"},
    "explorer_path": {"en": "Shortest Path", "ru": "Кратчайший путь"},
    "explorer_from": {"en": "From", "ru": "От"},
    "explorer_to": {"en": "To", "ru": "До"},
    "explorer_find_path": {"en": "Find Path", "ru": "Найти путь"},

    # Search tab
    "search_header": {"en": "Hybrid Search & Question Answering", "ru": "Гибридный Поиск и Ответы"},
    "search_input": {"en": "Ask a question about Ramayana", "ru": "Задайте вопрос о Рамаяне"},
    "search_placeholder": {"en": "Who is Rama? / What happened in Lanka?", "ru": "Кто такой Рама? / Что произошло на Ланке?"},
    "search_mode": {"en": "Retrieval mode", "ru": "Режим поиска"},
    "search_mode_hybrid": {"en": "Hybrid (Vector + Graph)", "ru": "Гибридный (Вектор + Граф)"},
    "search_mode_vector": {"en": "Vector only", "ru": "Только вектор"},
    "search_mode_graph": {"en": "Graph only", "ru": "Только граф"},
    "search_button": {"en": "Ask", "ru": "Спросить"},
    "search_thinking": {"en": "Searching and generating answer...", "ru": "Поиск и генерация ответа..."},
    "search_answer": {"en": "Answer", "ru": "Ответ"},
    "search_confidence": {"en": "Confidence", "ru": "Уверенность"},
    "search_sources": {"en": "Sources ({count})", "ru": "Источники ({count})"},
    "search_graph_ctx": {"en": "Graph Context", "ru": "Графовый контекст"},
    "search_no_results": {"en": "No results. Run pipeline first.", "ru": "Нет результатов. Запустите pipeline."},

    # Dashboard tab
    "dash_header": {"en": "Knowledge Graph Dashboard", "ru": "Дашборд Графа Знаний"},
    "dash_total_nodes": {"en": "Total Nodes", "ru": "Всего узлов"},
    "dash_total_rels": {"en": "Total Relationships", "ru": "Всего связей"},
    "dash_nodes_by_label": {"en": "Nodes by Label", "ru": "Узлы по типу"},
    "dash_rels_by_type": {"en": "Relationships by Type", "ru": "Связи по типу"},
    "dash_top_cooccur": {"en": "Top Co-occurrences", "ru": "Топ совместных упоминаний"},

    # Co-occurrence tab
    "cooccur_header": {"en": "Character Co-occurrence Network", "ru": "Сеть совместных упоминаний"},
    "cooccur_top_n": {"en": "Top N pairs", "ru": "Топ N пар"},
    "cooccur_kanda_filter": {"en": "Filter by Kanda", "ru": "Фильтр по Канде"},
    "cooccur_all": {"en": "All Kandas", "ru": "Все Канды"},
    "cooccur_pair": {"en": "Character Pair", "ru": "Пара персонажей"},
    "cooccur_count": {"en": "Co-mentions", "ru": "Совместные упоминания"},

    # Settings tab
    "settings_header": {"en": "Settings & Pipeline Controls", "ru": "Настройки и управление Pipeline"},
    "settings_config": {"en": "Current Configuration", "ru": "Текущая конфигурация"},
    "settings_stats": {"en": "Graph Statistics", "ru": "Статистика графа"},
    "settings_pipeline": {"en": "Pipeline Controls", "ru": "Управление Pipeline"},
    "settings_run_pipeline": {"en": "Run Full Pipeline", "ru": "Запустить Pipeline"},
    "settings_running": {"en": "Running pipeline...", "ru": "Pipeline выполняется..."},
    "settings_clear": {"en": "Clear Database", "ru": "Очистить базу"},
    "settings_clear_confirm": {"en": "Type DELETE to confirm", "ru": "Введите DELETE для подтверждения"},
    "settings_clear_button": {"en": "Clear All Data", "ru": "Удалить все данные"},
    "settings_cleared": {"en": "Deleted {count} nodes", "ru": "Удалено {count} узлов"},

    # Common
    "error": {"en": "Error: {msg}", "ru": "Ошибка: {msg}"},
    "no_data": {"en": "No data available", "ru": "Нет данных"},
}


def get_translator(lang: str = "en") -> Callable[..., str]:
    """Return a translator function t(key, **kwargs)."""

    def t(key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(key)
        if entry is None:
            return key
        text = entry.get(lang, entry.get("en", key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    return t
