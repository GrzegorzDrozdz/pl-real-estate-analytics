import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import CITY_COLORS, PRIMARY, TEXT_COLOR

_SQM_BINS   = [20, 30, 40, 50, 60, 70, 80, 100, 120, 150]
_SQM_LABELS = ["20–30", "30–40", "40–50", "50–60", "60–70", "70–80", "80–100", "100–120", "120–150"]

def render(sale_df, sel_cities: list[str]):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    st.markdown('<p class="section-header">Standard i Udogodnienia (Nasycenie rynku)</p>', unsafe_allow_html=True)
    _amenities_overview(sale_df)

    st.markdown("---")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown('<p class="section-header">Struktura typów budynków</p>', unsafe_allow_html=True)
        _building_types_bar(sale_df)

    with col_c2:
        st.markdown('<p class="section-header">Podaż według liczby pokoi</p>', unsafe_allow_html=True)
        _rooms_bar(sale_df)

    st.markdown("---")

    col_c3, col_c4 = st.columns(2)

    with col_c3:
        st.markdown('<p class="section-header">Rozkład metrażu mieszkań</p>', unsafe_allow_html=True)
        _sqm_distribution(sale_df)

    with col_c4:
        st.markdown('<p class="section-header">Struktura wiekowa zasobów</p>', unsafe_allow_html=True)
        _build_era_distribution(sale_df)


def _amenities_overview(sale_df):
    features = {
        "hasElevator": "Winda",
        "hasParkingSpace": "Parking / Garaż",
        "hasBalcony": "Balkon / Taras",
        "hasSecurity": "Ochrona / Monitoring",
        "hasStorageRoom": "Komórka lokatorska"
    }
    cols = st.columns(len(features))
    for i, (col_key, label) in enumerate(features.items()):
        if col_key in sale_df.columns:
            total = len(sale_df)
            count_yes = len(sale_df[sale_df[col_key].astype(str).str.lower().isin(['yes', 'true', '1'])])
            percent = (count_yes / total) * 100 if total > 0 else 0
            with cols[i]:
                st.metric(label, f"{percent:.1f}%")
                st.progress(percent / 100)


def _building_types_bar(sale_df):
    dist = sale_df["type_pl"].value_counts().reset_index()
    dist.columns = ["Typ", "Liczba"]
    fig = px.bar(
        dist, x="Typ", y="Liczba",
        color="Liczba",
        color_continuous_scale="Blues",
        title="Liczba ofert wg typu zabudowy"
    )
    fig.update_layout(height=400, coloraxis_showscale=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _rooms_bar(sale_df):
    dist = sale_df["rooms"].value_counts().sort_index().reset_index()
    dist.columns = ["Pokoje", "Liczba"]
    dist["Pokoje_label"] = dist["Pokoje"].apply(lambda x: f"{int(x)} pok.")
    fig = px.bar(
        dist, x="Pokoje_label", y="Liczba",
        color="Liczba",
        color_continuous_scale="Blues",
        labels={"Pokoje_label": "Liczba pokoi", "Liczba": "Liczba ofert"},
        title="Rozkład liczby pokoi w ofertach"
    )
    fig.update_layout(height=400, coloraxis_showscale=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _sqm_distribution(sale_df):
    df = sale_df.copy()
    df["sqm_bucket"] = pd.cut(df["squareMeters"], bins=_SQM_BINS, labels=_SQM_LABELS)
    dist = df["sqm_bucket"].value_counts().sort_index().reset_index()
    dist.columns = ["Metraż (m²)", "Liczba"]
    fig = px.bar(
        dist, x="Metraż (m²)", y="Liczba",
        color="Liczba", color_continuous_scale="Purples",
        title="Popularność przedziałów metrażowych",
    )
    fig.update_layout(height=400, coloraxis_showscale=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _build_era_distribution(sale_df):
    df = sale_df.dropna(subset=["buildYear"]).copy()
    df = df[(df["buildYear"] >= 1900) & (df["buildYear"] <= 2025)]
    df["era"] = pd.cut(
        df["buildYear"],
        bins=[1899, 1939, 1959, 1979, 1999, 2009, 2019, 2025],
        labels=["Do 1939", "1940–1959", "1960–1979", "1980–1999", "2000–2009", "2010–2019", "2020+"],
    )
    era_counts = df["era"].value_counts().sort_index().reset_index()
    era_counts.columns = ["Era budowy", "Liczba ofert"]
    fig = px.bar(
        era_counts, x="Era budowy", y="Liczba ofert",
        color="Liczba ofert", color_continuous_scale="Viridis"
    )
    fig.update_layout(height=400, coloraxis_showscale=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(apply_theme(fig), use_container_width=True)
