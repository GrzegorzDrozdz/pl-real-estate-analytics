import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from charts import apply_theme
from config import WARNING, SUCCESS, DANGER

def render(sale_df, sel_cities, all_cities):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    st.markdown('<p class="section-header">Cena vs Odległość od centrum</p>', unsafe_allow_html=True)

    col_sp1, col_sp2 = st.columns([1, 4])
    with col_sp1:
        sel_city_map = st.selectbox(
            "Wybierz miasto:",
            options=sel_cities if sel_cities else all_cities,
            key="map_city",
        )
        color_by = st.radio(
            "Kolorowanie:",
            ["Cena/m²", "Liczba pokoi", "Metraż"],
            key="map_color",
        )

    city_df = sale_df[sale_df["city_pl"] == sel_city_map].copy()

    color_map = {
        "Cena/m²": ("pricePerSqm", "Cena/m² (zł)", "Reds"),
        "Liczba pokoi": ("rooms", "Liczba pokoi", "Blues"),
        "Metraż": ("squareMeters", "Metraż (m²)", "Greens"),
    }
    color_col, color_label, color_scale = color_map[color_by]

    with col_sp2:
        if not city_df.empty:
            fig_dist = px.scatter(
                city_df.sample(min(3000, len(city_df)), random_state=42),
                x="centreDistance", y="pricePerSqm",
                color=color_col,
                color_continuous_scale=color_scale,
                size="squareMeters",
                size_max=14,
                opacity=0.7,
                labels={
                    "centreDistance": "Odległość od centrum (km)",
                    "pricePerSqm": "Cena za m² (zł)",
                    color_col: color_label,
                },
                title=f"{sel_city_map} – Odległość od centrum vs cena/m²",
                hover_data=["squareMeters", "rooms", "type_pl"],
            )
            # Add trendline manually
            sub = city_df[["centreDistance", "pricePerSqm"]].dropna()
            if len(sub) > 10:
                slope, intercept, _, _, _ = stats.linregress(sub["centreDistance"], sub["pricePerSqm"])
                x_range = np.linspace(sub["centreDistance"].min(), sub["centreDistance"].max(), 100)
                fig_dist.add_trace(go.Scatter(
                    x=x_range, y=slope * x_range + intercept,
                    mode="lines",
                    line=dict(color=WARNING, width=2.5, dash="dash"),
                    name="Trend liniowy",
                ))
            fig_dist.update_layout(height=480, title_font_size=14)
            st.plotly_chart(apply_theme(fig_dist), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Mapa geograficzna ofert</p>', unsafe_allow_html=True)

    map_df = sale_df.dropna(subset=["latitude", "longitude"]).copy()
    map_df = map_df[
        map_df["latitude"].between(49, 55) &
        map_df["longitude"].between(14, 24)
    ]

    if not map_df.empty:
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            map_sample = st.slider("Próbka punktów:", 500, min(10000, len(map_df)), min(3000, len(map_df)), 500)
            map_color_by = st.radio("Koloruj wg:", ["Cena/m²", "Miasto"], key="map_color2")

        map_sample_df = map_df.sample(min(map_sample, len(map_df)), random_state=42)

        with col_m2:
            if map_color_by == "Cena/m²":
                fig_map = px.scatter_mapbox(
                    map_sample_df,
                    lat="latitude", lon="longitude",
                    color="pricePerSqm",
                    color_continuous_scale="RdYlGn_r",
                    size="squareMeters", size_max=10,
                    opacity=0.7,
                    zoom=5.5,
                    center={"lat": 52.0, "lon": 19.5},
                    mapbox_style="carto-darkmatter",
                    hover_data=["city_pl", "price", "squareMeters", "rooms"],
                    labels={"pricePerSqm": "Cena/m² (zł)", "city_pl": "Miasto"},
                    title="Mapa ofert sprzedaży – cena/m²",
                )
            else:
                fig_map = px.scatter_mapbox(
                    map_sample_df,
                    lat="latitude", lon="longitude",
                    color="city_pl",
                    size="squareMeters", size_max=10,
                    opacity=0.7,
                    zoom=5.5,
                    center={"lat": 52.0, "lon": 19.5},
                    mapbox_style="carto-darkmatter",
                    hover_data=["pricePerSqm", "price", "squareMeters", "rooms"],
                    labels={"city_pl": "Miasto", "pricePerSqm": "Cena/m² (zł)"},
                    title="Mapa ofert sprzedaży – miasta",
                )
            fig_map.update_layout(height=520, title_font_size=14)
            st.plotly_chart(apply_theme(fig_map), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Wpływ odległości od infrastruktury na cenę</p>', unsafe_allow_html=True)

    infra_cols = {
        "schoolDistance": "Szkoła",
        "clinicDistance": "Przychodnia",
        "kindergartenDistance": "Przedszkole",
        "restaurantDistance": "Restauracja",
        "pharmacyDistance": "Apteka",
        "postOfficeDistance": "Poczta",
    }

    infra_data = []
    for col, label in infra_cols.items():
        if col in sale_df.columns:
            sub = sale_df[[col, "pricePerSqm"]].dropna()
            if not sub.empty:
                sub = sub[sub[col] < sub[col].quantile(0.95)]
                if len(sub) > 50:
                    corr = sub[col].corr(sub["pricePerSqm"])
                    infra_data.append({"Infrastruktura": label, "Korelacja z ceną/m²": corr})

    if infra_data:
        infra_df_plot = pd.DataFrame(infra_data).sort_values("Korelacja z ceną/m²")
        fig_infra = go.Figure(go.Bar(
            y=infra_df_plot["Infrastruktura"],
            x=infra_df_plot["Korelacja z ceną/m²"],
            orientation="h",
            marker_color=[SUCCESS if x > 0 else DANGER for x in infra_df_plot["Korelacja z ceną/m²"]],
            text=infra_df_plot["Korelacja z ceną/m²"].apply(lambda x: f"{x:+.3f}"),
            textposition="outside",
        ))
        fig_infra.update_layout(
            title="Korelacja odległości od infrastruktury z ceną/m² (ujemna = bliskość podwyższa cenę)",
            xaxis_title="Współczynnik korelacji Pearsona",
            height=360,
            title_font_size=13,
        )
        st.plotly_chart(apply_theme(fig_infra), use_container_width=True)