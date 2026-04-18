from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("data/veille_pqc.db")

st.set_page_config(page_title="Veille PQC", layout="wide")
st.title("Dashboard Veille PQC")

if not DB_PATH.exists():
    st.warning("Base SQLite introuvable. Lance d'abord la collecte.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(
    """
    SELECT source_name, title, published, url, score, category, sector_tags_json
    FROM items
    ORDER BY score DESC, published DESC
    """,
    conn,
)
conn.close()

if df.empty:
    st.info("Aucune donnée pour le moment.")
    st.stop()

categories = sorted([c for c in df["category"].fillna("other").unique().tolist() if c])
category_filter = st.multiselect("Catégories", categories, default=categories)
search = st.text_input("Recherche libre")

filtered = df[df["category"].fillna("other").isin(category_filter)].copy()
if search:
    mask = filtered["title"].str.contains(search, case=False, na=False) | filtered["source_name"].str.contains(search, case=False, na=False)
    filtered = filtered[mask]

col1, col2, col3 = st.columns(3)
col1.metric("Items", len(filtered))
col2.metric("Sources", filtered["source_name"].nunique())
col3.metric("Score moyen", round(filtered["score"].mean(), 1))

st.subheader("Répartition par catégorie")
st.bar_chart(filtered["category"].fillna("other").value_counts())

st.subheader("Derniers items")
st.dataframe(filtered[["published", "source_name", "category", "score", "title", "url"]], use_container_width=True)
