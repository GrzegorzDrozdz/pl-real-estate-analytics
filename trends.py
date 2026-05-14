import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import MONTH_NAMES, MONTH_ORDER, SUCCESS, DANGER


def render(sale_df, sale_df_full, sel_months: list[str], all_cities: list[str]):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    st.markdown('<p class="section-header">Dynamika cen – trendy miesięczne</p>', unsafe_allow_html=True)

    trend = (
        sale_df.groupby(["month_key", "month_label", "city_pl"])
        .agg(median_psqm=("pricePerSqm", "median"), count=("price", "count"))
        .reset_index()
    )
    trend["sort_idx"] = trend["month_key"].map(MONTH_ORDER)
    trend = trend.sort_values("sort_idx")

    top_cities = (
        sale_df.groupby("city_pl")["pricePerSqm"]
        .median()
        .sort_values(ascending=False)
        .head(8)
        .index.tolist()
    )

    col_sel, col_info = st.columns([2, 1])

    with col_sel:
        sel_trend_cities = st.multiselect(
            "Wybierz miasta do analizy trendu:",
            options=all_cities,
            default=top_cities[:6] if len(top_cities) >= 6 else top_cities,
            key="trend_cities",
        ) or top_cities[:6]

    with col_info:
        count_val = len(sale_df[sale_df["city_pl"].isin(sel_trend_cities)])
        st.markdown(
            f"<p style='text-align: right; color: gray; padding-top: 35px;'>Analiza <b>{count_val:,}</b> ofert sprzedaży</p>".replace(
                ",", " "),
            unsafe_allow_html=True
        )

    trend_filtered = trend[trend["city_pl"].isin(sel_trend_cities)]
    fig_trend = px.line(
        trend_filtered,
        x="month_label", y="median_psqm",
        color="city_pl",
        labels={"month_label": "Miesiąc", "median_psqm": "Mediana ceny/m² (zł)", "city_pl": "Miasto"},
        title="Zmiana mediany ceny/m² w czasie",
    )

    fig_trend.update_traces(line_width=2.5, marker=dict(size=8))
    fig_trend.update_layout(
        height=400,
        title_font_size=14,
        showlegend=False,
        margin=dict(r=80),
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )

    for trace in fig_trend.data:
        if trace.x is not None and len(trace.x) > 0:
            fig_trend.add_annotation(
                x=trace.x[-1], y=trace.y[-1],
                text=f"<b>{trace.name}</b>",
                showarrow=False, font=dict(color=trace.line.color, size=12),
                xanchor="left", xshift=8
            )

    st.plotly_chart(apply_theme(fig_trend), use_container_width=True)

    st.markdown("---")

    st.markdown('<p class="section-header">Zmiana cen: pierwszy vs ostatni miesiąc (%)</p>', unsafe_allow_html=True)

    all_months = sorted(sale_df_full["month_key"].unique())
    first_m = sel_months[0] if sel_months else all_months[0]
    last_m = sel_months[-1] if sel_months else all_months[-1]

    first_prices = sale_df_full[sale_df_full["month_key"] == first_m].groupby("city_pl")["pricePerSqm"].median()
    last_prices = sale_df_full[sale_df_full["month_key"] == last_m].groupby("city_pl")["pricePerSqm"].median()

    change = pd.DataFrame({"first": first_prices, "last": last_prices}).dropna()
    change["change_pct"] = (change["last"] - change["first"]) / change["first"] * 100
    change = change.reset_index().sort_values("last", ascending=True)
    change = change[change["city_pl"].isin(sel_trend_cities)]

    fig_change = go.Figure()
    for i, row in change.iterrows():
        color = SUCCESS if row["change_pct"] > 0 else DANGER
        fig_change.add_trace(go.Scatter(
            x=[row["first"], row["last"]], y=[row["city_pl"], row["city_pl"]],
            mode="markers+lines",
            line=dict(color=color, width=4),
            marker=dict(color=color, size=8),
            showlegend=False,
        ))
        fig_change.add_annotation(
            x=row["last"], y=row["city_pl"],
            text=f"<b>{row['change_pct']:+.1f}%</b>",
            showarrow=False, font=dict(color=color, size=11),
            xanchor="left" if row["change_pct"] > 0 else "right",
            xshift=10 if row["change_pct"] > 0 else -10
        )

    fig_change.update_layout(
        title=f"Wzrost/spadek ceny ({MONTH_NAMES.get(first_m, first_m)} → {MONTH_NAMES.get(last_m, last_m)})",
        xaxis_title="Cena zł/m²",
        height=min(600, 150 + len(change) * 30),
        title_font_size=14,
        margin=dict(r=50),
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    st.plotly_chart(apply_theme(fig_change), use_container_width=True)

    st.markdown("---")

    st.markdown('<p class="section-header">Heatmapa cen: miasto × miesiąc</p>', unsafe_allow_html=True)

    heatmap_df = sale_df[sale_df["city_pl"].isin(sel_trend_cities)]
    pivot = heatmap_df.groupby(["city_pl", "month_key"])["pricePerSqm"].median().unstack()
    col_labels = [MONTH_NAMES.get(m, m) for m in pivot.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=col_labels,
        y=pivot.index.tolist(),
        colorscale="RdYlGn_r",
        colorbar=dict(title="zł/m²"),
        text=[[f"{v:,.0f}".replace(",", " ") for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont_size=10,
    ))
    fig_heat.update_layout(
        title="Rozkład mediany ceny/m² w czasie",
        height=500,
        title_font_size=14,
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    st.plotly_chart(apply_theme(fig_heat), use_container_width=True)
