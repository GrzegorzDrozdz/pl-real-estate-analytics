import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import CITY_COLORS, PRIMARY, WARNING, GRID_COLOR, PLOT_BG, PAPER_BG, TEXT_COLOR

_AMENITIES = {
    "hasParkingSpace": "Miejsce parkingowe",
    "hasBalcony": "Balkon",
    "hasElevator": "Winda",
    "hasSecurity": "Ochrona",
    "hasStorageRoom": "Komórka lokal.",
}

SUCCESS = "#10b981"
DANGER = "#ef4444"


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
        col_m1, col_m2 = st.columns([3, 2])

        with col_m1:
            mask = np.triu(np.ones_like(corr_data, dtype=bool), k=0)
            corr_masked = corr_data.mask(mask)
            text_vals = [["" if pd.isna(v) else f"{v:.2f}" for v in row] for row in corr_masked.values]

            fig_corr = go.Figure(go.Heatmap(
                z=corr_masked.values,
                x=corr_labels,
                y=corr_labels,
                colorscale="RdBu",
                zmid=0,
                text=text_vals,
                texttemplate="%{text}",
                textfont_size=10,
                colorbar=dict(title="Wsp. r", thickness=15),
                hoverinfo="x+y+z",
            ))
            fig_corr.update_layout(
                title="Wzajemne korelacje cech (zależności)",
                height=500,
                title_font_size=14,
                yaxis_autorange="reversed",
                xaxis_showgrid=False,
                yaxis_showgrid=False,
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(apply_theme(fig_corr), use_container_width=True)

        with col_m2:
            if "pricePerSqm" in corr_data.columns:
                target_corr = corr_data["pricePerSqm"].drop("pricePerSqm").sort_values()
                df_target = target_corr.reset_index()
                df_target.columns = ["feature", "corr_value"]
                df_target["feature_pl"] = df_target["feature"].map(labels_pl)

                fig_bar = px.bar(
                    df_target,
                    x="corr_value",
                    y="feature_pl",
                    orientation="h",
                    color="corr_value",
                    color_continuous_scale="RdBu",
                    color_continuous_midpoint=0,
                    labels={"corr_value": "Siła wpływu (r)", "feature_pl": ""},
                    title="Co najbardziej wpływa na Cenę/m²?"
                )
                fig_bar.update_traces(textposition="outside", cliponaxis=False)
                fig_bar.update_layout(
                    height=500,
                    title_font_size=14,
                    coloraxis_showscale=False,
                    xaxis_title="Współczynnik korelacji (Pearson)",
                    xaxis_showgrid=False,
                    yaxis_showgrid=False,
                    margin=dict(r=30)
                )
                st.plotly_chart(apply_theme(fig_bar), use_container_width=True)

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown('<p class="section-header">Metraż vs Cena całkowita</p>', unsafe_allow_html=True)

        if not sale_df.empty:
            scatter_df = sale_df.copy()
            q_sqm = scatter_df["squareMeters"].quantile(0.99)
            q_price = scatter_df["price"].quantile(0.99)
            scatter_df = scatter_df[(scatter_df["squareMeters"] < q_sqm) & (scatter_df["price"] < q_price)]

            if "rooms" in scatter_df.columns:
                scatter_df["Pokoje"] = scatter_df["rooms"].apply(
                    lambda x: f"{int(x)} pok." if pd.notna(x) else "Inne"
                )
                scatter_df = scatter_df.sort_values("rooms")
                color_col = "Pokoje"
            else:
                color_col = None

            if len(scatter_df) > 3000:
                scatter_df = scatter_df.sample(3000, random_state=42)

            fig_sc = px.scatter(
                scatter_df,
                x="squareMeters",
                y="price",
                color=color_col,
                opacity=0.6,
                labels={
                    "squareMeters": "Metraż (m²)",
                    "price": "Cena całkowita (zł)",
                },
                title="Metraż vs Cena całkowita"
            )

            fig_sc.update_layout(
                height=450,
                title_font_size=13,
                xaxis_showgrid=False,
                yaxis_showgrid=False
            )
            st.plotly_chart(apply_theme(fig_sc), use_container_width=True)

    with col_f2:
        st.markdown('<p class="section-header">Wpływ udogodnień na cenę</p>', unsafe_allow_html=True)

        rows = []
        for col, label in _AMENITIES.items():
            if col not in sale_df.columns:
                continue
            grp = sale_df.groupby(col)["pricePerSqm"].median()
            if "yes" in grp.index and "no" in grp.index:
                diff_pct = (grp["yes"] - grp["no"]) / grp["no"] * 100
                rows.append({"Udogodnienie": label, "Różnica %": diff_pct})

        if rows:
            df_am = pd.DataFrame(rows).sort_values("Różnica %", ascending=True)
            fig_am = go.Figure(go.Bar(
                y=df_am["Udogodnienie"],
                x=df_am["Różnica %"],
                orientation="h",
                marker_color=[SUCCESS if x > 0 else DANGER for x in df_am["Różnica %"]],
                textposition="outside",
            ))
            fig_am.update_layout(
                title="Premia cenowa za udogodnienia (%)",
                xaxis_title="Różnica w medianie ceny/m² względem braku udogodnienia",
                height=400,
                title_font_size=13,
                xaxis_showgrid=False,
                yaxis_showgrid=False,
                margin=dict(t=50, b=50, l=150, r=50)
            )
            st.plotly_chart(apply_theme(fig_am), use_container_width=True)
        else:
            st.info("Brak wystarczających danych o udogodnieniach w obecnym filtrze.")

    st.markdown("---")
    st.markdown('<p class="section-header">Analiza piętra a cena</p>', unsafe_allow_html=True)

    floor_df = sale_df.dropna(subset=["floor"]).copy()
    if not floor_df.empty:
        floor_df = floor_df[floor_df["floor"].between(0, 20)]
        floor_stats = floor_df.groupby("floor")["pricePerSqm"].agg(["median", "count"]).reset_index()
        floor_stats.columns = ["Piętro", "Mediana ceny/m²", "Liczba ofert"]

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
            mode="lines",
            yaxis="y2",
        ))
        fig_floor.update_layout(
            title="Cena/m² i liczba ofert według piętra",
            yaxis=dict(title="Mediana ceny/m² (zł)", showgrid=False),
            yaxis2=dict(title="Liczba ofert", overlaying="y", side="right", showgrid=False),
            xaxis=dict(title="Piętro", showgrid=False),
            height=450,
            title_font_size=14,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
        )
        st.plotly_chart(apply_theme(fig_floor), use_container_width=True)
