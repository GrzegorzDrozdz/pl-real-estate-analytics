import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import MONTH_NAMES

def render(sale_df_full, rent_df_full, sale_df, rent_df):
    if sale_df_full.empty or rent_df_full.empty:
        st.warning("⚠️ Brak dostępnych danych do zestawienia parametrów inwestycyjnych.")
        return

    common_cities = sorted(set(sale_df["city_pl"].unique()) & set(rent_df["city_pl"].unique()))

    if not common_cities:
        st.warning("⚠️ Brak wspólnych miast w obu zbiorach danych.")
        return

    st.markdown('<p class="section-header">Analiza Rentowności Inwestycji</p>', unsafe_allow_html=True)

    sale_city_m = sale_df[sale_df["city_pl"].isin(common_cities)].groupby("city_pl").agg(
        med_sale_psqm=("pricePerSqm", "median"),
        med_sale_price=("price", "median")
    ).reset_index()

    rent_city_m = rent_df[rent_df["city_pl"].isin(common_cities)].groupby("city_pl").agg(
        med_rent_psqm=("pricePerSqm", "median"),
        med_rent=("price", "median")
    ).reset_index()

    combined = sale_city_m.merge(rent_city_m, on="city_pl")
    combined["gross_yield"] = (combined["med_rent"] * 12) / combined["med_sale_price"] * 100
    combined["payback_years"] = combined["med_sale_price"] / (combined["med_rent"] * 12)

    col_rv1, col_rv2 = st.columns(2)

    with col_rv1:
        df_yield = combined.sort_values("gross_yield", ascending=True)
        fig_yield = px.bar(
            df_yield, x="gross_yield", y="city_pl",
            orientation="h",
            color="gross_yield",
            color_continuous_scale="Bluyl",
            labels={"city_pl": "Miasto", "gross_yield": "ROI (%)"},
            title="Rentowność najmu (Brutto ROI)",
        )
        fig_yield.update_layout(
            height=480,
            coloraxis_showscale=False,
            title_font_size=14,
            xaxis_showgrid=False,
            yaxis_showgrid=False
        )
        st.plotly_chart(apply_theme(fig_yield), use_container_width=True)

    with col_rv2:
        df_payback = combined.sort_values("payback_years", ascending=False)
        fig_payback = px.bar(
            df_payback, x="payback_years", y="city_pl",
            orientation="h",
            color="payback_years",
            color_continuous_scale="Mint",
            labels={"city_pl": "Miasto", "payback_years": "Lata"},
            title="Szacowany okres zwrotu",
        )
        fig_payback.update_layout(
            height=480,
            coloraxis_showscale=False,
            title_font_size=14,
            xaxis_showgrid=False,
            yaxis_showgrid=False
        )
        st.plotly_chart(apply_theme(fig_payback), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Trend czynszów najmu</p>', unsafe_allow_html=True)

    col_sel, col_info = st.columns([2, 1])
    with col_sel:
        sel_rent_cities = st.multiselect("Porównaj miasta:", options=common_cities, default=common_cities[:5],
                                         key="rent_cities")

    if not sel_rent_cities: sel_rent_cities = common_cities[:5]

    with col_info:
        count_val = len(rent_df[rent_df["city_pl"].isin(sel_rent_cities)])
        st.markdown(
            f"<p style='text-align: right; color: #888; padding-top: 35px;'>Próba: <b>{count_val:,}</b> ofert</p>".replace(
                ",", " "), unsafe_allow_html=True)

    rent_trend = rent_df[rent_df["city_pl"].isin(sel_rent_cities)].groupby(["month_key", "month_label", "city_pl"])[
        "pricePerSqm"].median().reset_index()
    month_order = {k: i for i, k in enumerate(MONTH_NAMES.keys())}
    rent_trend = rent_trend.sort_values(by="month_key", key=lambda x: x.map(month_order))

    fig_trend = px.line(
        rent_trend, x="month_label", y="pricePerSqm", color="city_pl",
        labels={"month_label": "Miesiąc", "pricePerSqm": "zł/m²"},
        title="Mediana czynszu / m² w czasie"
    )
    fig_trend.update_traces(line_width=3, marker=dict(size=6))
    fig_trend.update_layout(
        height=450,
        showlegend=False,
        margin=dict(r=120),
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    fig_trend.update_yaxes(rangemode="tozero")

    for trace in fig_trend.data:
        fig_trend.add_annotation(
            x=trace.x[-1], y=trace.y[-1], text=f" {trace.name}",
            showarrow=False, xanchor="left", font=dict(size=12, color=trace.line.color)
        )
    st.plotly_chart(apply_theme(fig_trend), use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Macierz Inwestycyjna: Bariera wejścia vs Opłacalność</p>',
                unsafe_allow_html=True)

    med_x = combined["med_sale_psqm"].median()
    med_y = combined["gross_yield"].median()

    fig_matrix = px.scatter(
        combined,
        x="med_sale_psqm",
        y="gross_yield",
        text="city_pl",
        labels={
            "med_sale_psqm": "Cena zakupu / m² (zł)",
            "gross_yield": "Stopa zwrotu brutto (%)",
        },
        title="Podział rynków wg kosztu wejścia i rentowności"
    )

    fig_matrix.update_traces(
        marker=dict(size=14, color="#3b82f6", opacity=0.8, line=dict(width=1, color="white")),
        textposition="top center",
        textfont_size=12
    )

    fig_matrix.add_vline(x=med_x, line_width=1.5, line_dash="dash", line_color="#888888", opacity=0.6)
    fig_matrix.add_hline(y=med_y, line_width=1.5, line_dash="dash", line_color="#888888", opacity=0.6)

    annotations = [
        dict(x=0.02, y=0.98, text="<b>Tanie i Zyskowne</b><br><i>(Okazje)</i>", xanchor="left", yanchor="top",
             color="#10b981"),
        dict(x=0.98, y=0.98, text="<b>Drogie i Zyskowne</b><br><i>(Premium)</i>", xanchor="right", yanchor="top",
             color="#f59e0b"),
        dict(x=0.98, y=0.02, text="<b>Drogie i Niskodochodowe</b><br><i>(Ryzyko kapitałowe)</i>", xanchor="right",
             yanchor="bottom", color="#ef4444"),
        dict(x=0.02, y=0.02, text="<b>Tanie i Niskodochodowe</b><br><i>(Stagnacja)</i>", xanchor="left",
             yanchor="bottom", color="#6b7280"),
    ]

    for ann in annotations:
        fig_matrix.add_annotation(
            xref="paper", yref="paper",
            x=ann["x"], y=ann["y"],
            text=ann["text"],
            showarrow=False,
            xanchor=ann["xanchor"], yanchor=ann["yanchor"],
            font=dict(color=ann["color"], size=12),
            bgcolor="rgba(128, 128, 128, 0.1)",
            bordercolor=ann["color"],
            borderwidth=1,
            borderpad=6
        )

    fig_matrix.update_xaxes(rangemode="tozero", showgrid=False, zeroline=True, zerolinecolor="rgba(128,128,128,0.2)")
    fig_matrix.update_yaxes(rangemode="tozero", showgrid=False, zeroline=True, zerolinecolor="rgba(128,128,128,0.2)")

    fig_matrix.update_layout(
        height=600,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    st.plotly_chart(apply_theme(fig_matrix), use_container_width=True)

    st.markdown('<p class="section-header">Zestawienie szczegółowe</p>', unsafe_allow_html=True)
    df_tab = combined.sort_values("gross_yield", ascending=False).copy()

    fmt = lambda x: f"{x:,.0f}".replace(",", " ")
    df_tab["med_sale_price"] = (df_tab["med_sale_price"] / 1000).apply(lambda x: f"{x:,.0f} tys. zł".replace(",", " "))
    df_tab["med_sale_psqm"] = df_tab["med_sale_psqm"].apply(lambda x: f"{fmt(x)} zł")
    df_tab["med_rent"] = df_tab["med_rent"].apply(lambda x: f"{fmt(x)} zł")
    df_tab["gross_yield"] = df_tab["gross_yield"].apply(lambda x: f"{x:.2f}%")
    df_tab["payback_years"] = df_tab["payback_years"].apply(lambda x: f"{x:.1f} lat")

    df_tab.columns = ["Miasto", "Cena m²", "Mediana ceny", "Czynsz m²", "Mediana czynszu", "ROI", "Zwrot"]
    st.dataframe(df_tab[["Miasto", "Mediana ceny", "Cena m²", "Mediana czynszu", "ROI", "Zwrot"]],
                 use_container_width=True, hide_index=True)
