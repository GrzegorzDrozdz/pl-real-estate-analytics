import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import CITY_COLORS, PRIMARY, WARNING, GRID_COLOR, PLOT_BG, PAPER_BG, TEXT_COLOR

def render(sale_df, sel_cities):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    st.markdown('<p class="section-header">Macierz korelacji cech numerycznych</p>', unsafe_allow_html=True)

    num_cols = [
        "pricePerSqm", "squareMeters", "rooms", "floor", "floorCount",
        "buildYear", "centreDistance", "poiCount",
        "schoolDistance", "clinicDistance", "restaurantDistance", "pharmacyDistance",
    ]
    labels_pl = {
        "pricePerSqm": "Cena/m²", "squareMeters": "Metraż", "rooms": "Pokoje",
        "floor": "Piętro", "floorCount": "Liczba pięter", "buildYear": "Rok budowy",
        "centreDistance": "Odl. od centrum", "poiCount": "Liczba POI",
        "schoolDistance": "Odl. szkoła", "clinicDistance": "Odl. przychodnia",
        "restaurantDistance": "Odl. restauracja", "pharmacyDistance": "Odl. apteka",
    }

    valid_cols = [c for c in num_cols if c in sale_df.columns]
    corr_data = sale_df[valid_cols].dropna().corr()
    corr_labels = [labels_pl.get(c, c) for c in corr_data.columns]

    if not corr_data.empty:
        fig_corr = go.Figure(go.Heatmap(
            z=corr_data.values,
            x=corr_labels,
            y=corr_labels,
            colorscale="RdBu",
            zmid=0,
            text=[[f"{v:.2f}" for v in row] for row in corr_data.values],
            texttemplate="%{text}",
            textfont_size=9,
            colorbar=dict(title="r"),
        ))
        fig_corr.update_layout(
            title="Macierz korelacji Pearsona – cechy numeryczne",
            height=580,
            title_font_size=14,
        )
        st.plotly_chart(apply_theme(fig_corr), use_container_width=True)

    st.markdown("---")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown('<p class="section-header">Metraż vs Cena całkowita</p>', unsafe_allow_html=True)

        sel_city_scatter = st.selectbox(
            "Miasto:",
            options=["Wszystkie"] + list(sel_cities),
            key="scatter_city",
        )

        scatter_df = sale_df if sel_city_scatter == "Wszystkie" else sale_df[sale_df["city_pl"] == sel_city_scatter]
        if not scatter_df.empty:
            scatter_df = scatter_df.sample(min(2000, len(scatter_df)), random_state=42)

            fig_sc = px.scatter(
                scatter_df,
                x="squareMeters", y="price",
                color="rooms",
                color_continuous_scale="Turbo",
                opacity=0.6,
                trendline="ols",
                labels={
                    "squareMeters": "Metraż (m²)",
                    "price": "Cena (zł)",
                    "rooms": "Liczba pokoi",
                },
                title=f"Metraż vs Cena – {sel_city_scatter}",
            )
            fig_sc.update_layout(height=400, title_font_size=13)
            st.plotly_chart(apply_theme(fig_sc), use_container_width=True)

    with col_f2:
        st.markdown('<p class="section-header">Rozkład ceny/m² – histogram + KDE</p>', unsafe_allow_html=True)

        cities_hist = st.multiselect(
            "Miasta do porównania:",
            options=sel_cities,
            default=sel_cities[:4] if len(sel_cities) >= 4 else sel_cities,
            key="hist_cities",
        )

        if not cities_hist:
            cities_hist = sel_cities[:4]

        fig_hist = go.Figure()
        for i, city in enumerate(cities_hist):
            subset = sale_df[sale_df["city_pl"] == city]["pricePerSqm"].dropna()
            fig_hist.add_trace(go.Histogram(
                x=subset,
                name=city,
                opacity=0.55,
                nbinsx=40,
                marker_color=CITY_COLORS[i % len(CITY_COLORS)],
            ))
        fig_hist.update_layout(
            barmode="overlay",
            xaxis_title="Cena/m² (zł)",
            yaxis_title="Liczba ofert",
            title="Rozkład cen/m² – porównanie miast",
            height=400,
            title_font_size=13,
        )
        st.plotly_chart(apply_theme(fig_hist), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Analiza piętra a cena</p>', unsafe_allow_html=True)

    floor_df = sale_df.dropna(subset=["floor"]).copy()
    if not floor_df.empty:
        floor_df = floor_df[floor_df["floor"].between(0, 20)]
        floor_stats = floor_df.groupby("floor")["pricePerSqm"].agg(["median", "count"]).reset_index()
        floor_stats.columns = ["Piętro", "Mediana ceny/m²", "Liczba ofert"]

        col_fl1, col_fl2 = st.columns(2)

        with col_fl1:
            fig_floor = go.Figure()
            fig_floor.add_trace(go.Bar(
                x=floor_stats["Piętro"],
                y=floor_stats["Mediana ceny/m²"],
                name="Mediana ceny/m²",
                marker_color=PRIMARY,
                yaxis="y",
            ))
            fig_floor.add_trace(go.Scatter(
                x=floor_stats["Piętro"],
                y=floor_stats["Liczba ofert"],
                name="Liczba ofert",
                line=dict(color=WARNING, width=2),
                mode="lines+markers",
                yaxis="y2",
            ))
            fig_floor.update_layout(
                title="Cena/m² i liczba ofert według piętra",
                yaxis=dict(title="Mediana ceny/m² (zł)", gridcolor=GRID_COLOR),
                yaxis2=dict(title="Liczba ofert", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
                xaxis_title="Piętro",
                height=400,
                title_font_size=13,
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(apply_theme(fig_floor), use_container_width=True)

        with col_fl2:
            st.markdown('<p class="section-header">Własność a cena</p>', unsafe_allow_html=True)

            ownership_stats = (
                sale_df.groupby(["city_pl", "ownership"])["pricePerSqm"]
                .median().reset_index()
            )
            ownership_stats = ownership_stats[ownership_stats["city_pl"].isin(sel_cities[:8])]
            ownership_stats["ownership"] = ownership_stats["ownership"].map({
                "condominium": "Odrębna własność",
                "cooperative": "Spółdzielcze",
            }).fillna(ownership_stats["ownership"])

            fig_own = px.bar(
                ownership_stats,
                x="city_pl", y="pricePerSqm",
                color="ownership",
                barmode="group",
                labels={"city_pl": "Miasto", "pricePerSqm": "Mediana ceny/m² (zł)", "ownership": "Forma własności"},
                title="Cena/m² wg formy własności",
            )
            fig_own.update_layout(height=400, title_font_size=13)
            st.plotly_chart(apply_theme(fig_own), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Profil typowego mieszkania w każdym mieście</p>', unsafe_allow_html=True)

    radar_cities = st.multiselect(
        "Wybierz do 5 miast do porównania radarowego:",
        options=sel_cities,
        default=sel_cities[:5] if len(sel_cities) >= 5 else sel_cities,
        key="radar_cities",
    )
    if not radar_cities:
        radar_cities = sel_cities[:5]

    radar_metrics = {
        "pricePerSqm": "Cena/m²",
        "squareMeters": "Metraż",
        "rooms": "Pokoje",
        "centreDistance": "Odl. centrum",
        "buildYear": "Rok budowy",
        "poiCount": "Liczba POI",
    }

    radar_data = sale_df[sale_df["city_pl"].isin(radar_cities)].groupby("city_pl")[list(radar_metrics.keys())].median()
    if not radar_data.empty:
        radar_norm = (radar_data - radar_data.min()) / (radar_data.max() - radar_data.min() + 1e-9)
        radar_norm["centreDistance"] = 1 - radar_norm["centreDistance"]

        fig_radar = go.Figure()
        for i, city in enumerate(radar_cities):
            if city in radar_norm.index:
                vals = radar_norm.loc[city].tolist()
                vals.append(vals[0])
                labels = list(radar_metrics.values()) + [list(radar_metrics.values())[0]]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals, theta=labels,
                    fill="toself",
                    name=city,
                    line_color=CITY_COLORS[i % len(CITY_COLORS)],
                    fillcolor=CITY_COLORS[i % len(CITY_COLORS)],
                    opacity=0.25,
                ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], gridcolor=GRID_COLOR),
                angularaxis=dict(gridcolor=GRID_COLOR),
                bgcolor=PLOT_BG,
            ),
            title="Radar: znormalizowany profil miast (im wyżej = lepiej)",
            height=500,
            title_font_size=14,
            paper_bgcolor=PAPER_BG,
            font=dict(color=TEXT_COLOR),
        )
        st.plotly_chart(fig_radar, use_container_width=True)