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

    st.markdown('<p class="section-header">Analiza przestrzenna ofert</p>', unsafe_allow_html=True)

    map_df = sale_df.dropna(subset=["latitude", "longitude"]).copy()

    col_m1, col_m2 = st.columns([1, 4])

    with col_m1:
        st.info(
            "💡 **Wskazówka:** Użyj panelu bocznego, aby przefiltrować zakres cen, metraż lub liczbę pokoi. Mapa zaktualizuje się automatycznie.")

        map_view_options = ["Cała Polska"] + sorted(all_cities)
        selected_view = st.selectbox(
            "Zakres mapy:",
            options=map_view_options,
            index=0,
            key="spatial_city_view"
        )

        map_color_by = st.radio(
            "Koloruj według:",
            ["Cena/m²", "Cena całkowita", "Liczba pokoi"],
            key="spatial_color_map"
        )

    if selected_view == "Cała Polska":
        display_df = map_df.sample(min(8000, len(map_df)), random_state=42)
        center_coords = {"lat": 52.0, "lon": 19.5}
        zoom_level = 5.2
        map_title = "Rozkład ofert w całej Polsce (próbka)"
    else:
        display_df = map_df[map_df["city_pl"] == selected_view]

        if not display_df.empty:
            center_coords = {
                "lat": display_df["latitude"].mean(),
                "lon": display_df["longitude"].mean()
            }
            zoom_level = 11.5
        else:
            center_coords = {"lat": 52.0, "lon": 19.5}
            zoom_level = 5

        map_title = f"Wszystkie oferty w mieście: {selected_view} ({len(display_df)} punktów)"

    with col_m2:
        if not display_df.empty:
            color_map_config = {
                "Cena/m²": ("pricePerSqm", "RdYlGn_r", "Cena/m² (zł)"),
                "Cena całkowita": ("price", "RdYlGn_r", "Cena całkowita (zł)"),
                "Liczba pokoi": ("rooms", "Blues", "Liczba pokoi")
            }
            color_col, color_scale, color_label = color_map_config[map_color_by]

            fig_map = px.scatter_mapbox(
                display_df,
                lat="latitude", lon="longitude",
                color=color_col,
                color_continuous_scale=color_scale,
                size="squareMeters",
                size_max=10 if selected_view != "Cała Polska" else 6,
                opacity=0.7,
                zoom=zoom_level,
                center=center_coords,
                mapbox_style="carto-darkmatter",
                hover_data={
                    "latitude": False,
                    "longitude": False,
                    "city_pl": True,
                    "price": ":,.0f zł",
                    "pricePerSqm": ":,.0f zł",
                    "squareMeters": True,
                    "rooms": True
                },
                labels={"price": "Cena", "pricePerSqm": "Cena/m²", "rooms": "Pokoje", "city_pl": "Miasto"},
                title=map_title,
            )
            fig_map.update_layout(
                height=650,
                margin=dict(t=50, b=0, l=0, r=0),
                coloraxis_colorbar=dict(title=color_label)
            )
            st.plotly_chart(apply_theme(fig_map), use_container_width=True)
        else:
            st.info(f"Brak danych spełniających wybrane filtry dla: {selected_view}")
