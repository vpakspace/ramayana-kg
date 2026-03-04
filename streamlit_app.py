"""Ramayana Knowledge Graph — Streamlit UI (port 8507)."""

from __future__ import annotations

import plotly.express as px
import streamlit as st
from neo4j import GraphDatabase

from ramayana_kg.config import settings
from ramayana_kg.graph.queries import (
    co_occurrence,
    family_tree,
    get_entity_relationships,
    get_entity_verses,
    search_entities,
    shortest_path,
)
from ramayana_kg.graph.schema import clear_database, get_stats
from ramayana_kg.rag.generator import generate_answer
from ui.i18n import get_translator

KANDA_NAMES = {
    1: "Bala Kanda", 2: "Ayodhya Kanda", 3: "Aranya Kanda",
    4: "Kishkindha Kanda", 5: "Sundara Kanda", 6: "Yuddha Kanda",
}


@st.cache_resource
def get_driver():
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def main():
    st.set_page_config(page_title="Ramayana KG", page_icon="🏛️", layout="wide")

    lang = st.sidebar.selectbox("🌐 Language", ["en", "ru"], index=0)
    t = get_translator(lang)

    st.title(t("app_title"))
    st.caption(t("app_subtitle"))

    driver = get_driver()
    db = settings.neo4j_database

    tabs = st.tabs([
        t("tab_explorer"), t("tab_search"), t("tab_dashboard"),
        t("tab_cooccurrence"), t("tab_settings"),
    ])

    # --- Tab 1: KG Explorer ---
    with tabs[0]:
        _render_explorer(driver, db, t)

    # --- Tab 2: Hybrid Search ---
    with tabs[1]:
        _render_search(driver, db, t, lang=lang)

    # --- Tab 3: Dashboard ---
    with tabs[2]:
        _render_dashboard(driver, db, t)

    # --- Tab 4: Co-occurrence ---
    with tabs[3]:
        _render_cooccurrence(driver, db, t)

    # --- Tab 5: Settings ---
    with tabs[4]:
        _render_settings(driver, db, t)


def _render_explorer(driver, db, t):
    query = st.text_input(t("explorer_search"), placeholder=t("explorer_placeholder"))
    if query:
        results = search_entities(driver, query, limit=10, database=db)
        if results:
            st.subheader(t("explorer_results"))
            for r in results:
                with st.expander(f"**{r['name']}** ({r['label']}) — score: {r['score']:.3f}"):
                    st.write(r.get("description", ""))

                    rels = get_entity_relationships(driver, r["name"], database=db)
                    if rels:
                        st.markdown(f"**{t('explorer_relationships')}**")
                        for rel in rels:
                            st.write(f"  {rel['direction']} {rel['type']} — {rel['other']}")

                    if r["label"] == "Character":
                        fam = family_tree(driver, r["name"], database=db)
                        if fam:
                            st.markdown(f"**{t('explorer_family')}**")
                            for f in fam:
                                st.write(f"  {f['relation']} — {f['name']}")

                    verses = get_entity_verses(driver, r["name"], limit=3, database=db)
                    if verses:
                        st.markdown(f"**{t('explorer_verses')}**")
                        for v in verses:
                            st.caption(f"[{v['verse_id']}] {v['text'][:200]}...")
        else:
            st.info(t("no_data"))

    # Shortest path finder
    st.divider()
    st.subheader(t("explorer_path"))
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        source = st.text_input(t("explorer_from"), value="Rama")
    with col2:
        target = st.text_input(t("explorer_to"), value="Ravana")
    with col3:
        st.write("")
        st.write("")
        if st.button(t("explorer_find_path")):
            path = shortest_path(driver, source, target, database=db)
            if path:
                for step in path:
                    st.write(f"➡️ {step}")
            else:
                st.warning(t("no_data"))


def _render_search(driver, db, t, lang="en"):
    st.subheader(t("search_header"))

    mode_options = {
        t("search_mode_hybrid"): "hybrid",
        t("search_mode_vector"): "vector",
        t("search_mode_graph"): "graph",
    }
    mode_label = st.radio(t("search_mode"), list(mode_options.keys()), horizontal=True)
    mode = mode_options[mode_label]

    question = st.text_input(t("search_input"), placeholder=t("search_placeholder"))
    if st.button(t("search_button")) and question:
        with st.spinner(t("search_thinking")):
            result = generate_answer(
                question, driver, mode=mode,
                database=db, language=lang,
            )

        st.markdown(f"### {t('search_answer')}")
        st.write(result.answer)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(t("search_confidence"), f"{result.confidence:.2f}")
        with col2:
            st.write(f"**Mode**: {result.mode}")

        if result.sources:
            with st.expander(t("search_sources", count=len(result.sources))):
                for src in result.sources:
                    st.caption(f"[{src.verse_id}] score={src.score:.3f}")
                    st.write(src.text[:300])
                    st.divider()

        if result.graph_context and result.graph_context.entities:
            with st.expander(t("search_graph_ctx")):
                for e in result.graph_context.entities:
                    st.write(f"**{e['name']}** ({e.get('label', '')}): {e.get('description', '')}")
                if result.graph_context.paths:
                    st.markdown("**Paths:**")
                    for p in result.graph_context.paths[:10]:
                        st.write(f"  {p}")


def _render_dashboard(driver, db, t):
    st.subheader(t("dash_header"))
    stats = get_stats(driver, database=db)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(t("dash_total_nodes"), stats["total_nodes"])
    with col2:
        st.metric(t("dash_total_rels"), stats["total_relationships"])

    if stats["nodes_by_label"]:
        st.markdown(f"### {t('dash_nodes_by_label')}")
        labels = list(stats["nodes_by_label"].keys())
        values = list(stats["nodes_by_label"].values())
        fig = px.bar(x=labels, y=values, labels={"x": "Label", "y": "Count"})
        st.plotly_chart(fig, use_container_width=True)

    if stats["relationships_by_type"]:
        st.markdown(f"### {t('dash_rels_by_type')}")
        types = list(stats["relationships_by_type"].keys())
        counts = list(stats["relationships_by_type"].values())
        fig = px.pie(names=types, values=counts)
        st.plotly_chart(fig, use_container_width=True)


def _render_cooccurrence(driver, db, t):
    st.subheader(t("cooccur_header"))

    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider(t("cooccur_top_n"), 5, 50, 20)
    with col2:
        kanda_options: dict[str, int | None] = {t("cooccur_all"): None}
        kanda_options.update({v: k for k, v in KANDA_NAMES.items()})
        kanda_label = st.selectbox(t("cooccur_kanda_filter"), list(kanda_options.keys()))
        kanda_num = kanda_options[kanda_label]

    pairs = co_occurrence(driver, top_n=top_n, kanda_num=kanda_num, database=db)
    if pairs:
        # Table
        import pandas as pd
        df = pd.DataFrame(pairs)
        df.columns = [t("cooccur_pair") + " 1", t("cooccur_pair") + " 2", t("cooccur_count")]
        st.dataframe(df, use_container_width=True)

        # Bar chart
        labels = [f"{p['char1']} & {p['char2']}" for p in pairs[:15]]
        counts = [p["count"] for p in pairs[:15]]
        fig = px.bar(x=labels, y=counts, labels={"x": "Pair", "y": "Count"})
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_data"))


def _render_settings(driver, db, t):
    st.subheader(t("settings_header"))

    # Config display
    with st.expander(t("settings_config")):
        st.json({
            "neo4j_uri": settings.neo4j_uri,
            "neo4j_database": settings.neo4j_database,
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "extraction_batch_size": settings.extraction_batch_size,
            "top_k_vector": settings.top_k_vector,
            "top_k_final": settings.top_k_final,
            "graph_depth": settings.graph_depth,
        })

    # Stats
    with st.expander(t("settings_stats")):
        stats = get_stats(driver, database=db)
        st.json(stats)

    # Clear database
    st.divider()
    st.markdown(f"### {t('settings_clear')}")
    confirm = st.text_input(t("settings_clear_confirm"))
    if st.button(t("settings_clear_button")) and confirm == "DELETE":
        count = clear_database(driver, database=db)
        st.success(t("settings_cleared", count=count))


if __name__ == "__main__":
    main()
