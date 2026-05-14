import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import CITY_COLORS, MONTH_NAMES


def render(sale_df):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    st.markdown('<p class="section-header">Mediana ceny za m² według miasta</p>', unsafe_allow_html=True)

    city_stats = (
        sale_df.groupby("city_pl")
        .agg(
            median_psqm=("pricePerSqm", "median"),
            median_price=("price", "median"),
            count=("price", "count"),
            median_sqm=("squareMeters", "median"),
        )
        .reset_index()
        .sort_values("median_psqm", ascending=True)
    )

    fig = px.bar(
        city_stats, x="median_psqm", y="city_pl",
        orientation="h",
        color="median_psqm",
        color_continuous_scale="Blues",
        labels={"city_pl": "Miasto", "median_psqm": "Mediana ceny/m²"},
        title="Ranking miast wg mediany ceny za m²",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        height=500,
        title_font_size=14,
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    st.plotly_chart(apply_theme(fig), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Rozkład cen w miastach</p>', unsafe_allow_html=True)

    cities_sorted = (
        sale_df.groupby("city_pl")["pricePerSqm"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig3 = go.Figure()
    for i, city in enumerate(cities_sorted):
        subset = sale_df[sale_df["city_pl"] == city]["pricePerSqm"]
        fig3.add_trace(go.Violin(
            x=[city] * len(subset),
            y=subset,
            name=city,
            box_visible=True,
            meanline_visible=True,
            line_color=CITY_COLORS[i % len(CITY_COLORS)],
            fillcolor=CITY_COLORS[i % len(CITY_COLORS)],
            opacity=0.6,
            showlegend=False,
        ))
    fig3.update_layout(
        title="Violin Plot – rozkład ceny/m² w każdym mieście",
        yaxis_title="Cena za m² (zł)",
        height=420,
        title_font_size=14,
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    st.plotly_chart(apply_theme(fig3), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Statystyki według miast</p>', unsafe_allow_html=True)

    display = city_stats.sort_values("median_psqm", ascending=False).copy()
    display["median_psqm"]  = display["median_psqm"].apply(lambda x: f"{x:,.0f} zł".replace(",", " "))
    display["median_price"] = display["median_price"].apply(lambda x: f"{x/1e3:,.0f} tys. zł".replace(",", " "))
    display["median_sqm"]   = display["median_sqm"].apply(lambda x: f"{x:.1f} m²")
    display.columns = ["Miasto", "Mediana ceny/m²", "Mediana ceny", "Liczba ofert", "Mediana metrażu"]
    st.dataframe(display.reset_index(drop=True), use_container_width=True, height=400)