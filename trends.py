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

    col_controls, col_chart = st.columns([1, 3])

    with col_controls:
        sel_trend_cities = st.multiselect(
            "Pokaż miasta:",
            options=all_cities,
            default=top_cities[:6] if len(top_cities) >= 6 else top_cities,
            key="trend_cities",
        ) or top_cities[:6]

        st.checkbox("Pokaż trend (LOWESS)", value=True, key="show_lowess")

    with col_chart:
        fig_trend = px.line(
            trend[trend["city_pl"].isin(sel_trend_cities)],
            x="month_label", y="median_psqm",
            color="city_pl",
            markers=True,
            labels={"month_label": "Miesiąc", "median_psqm": "Mediana ceny/m² (zł)", "city_pl": "Miasto"},
            title="Trendy mediany ceny/m² w czasie",
        )
        fig_trend.update_traces(line_width=2.5, marker_size=8)
        fig_trend.update_layout(height=400, title_font_size=14)
        st.plotly_chart(apply_theme(fig_trend), use_container_width=True)

    st.markdown("---")
    col_t3, col_t4 = st.columns(2)

    with col_t3:
        st.markdown('<p class="section-header">Zmiana cen: pierwszy vs ostatni miesiąc (%)</p>', unsafe_allow_html=True)
        _price_change_chart(sale_df, sale_df_full, sel_months)

    with col_t4:
        st.markdown('<p class="section-header">Liczba ofert w czasie</p>', unsafe_allow_html=True)
        _supply_chart(sale_df, sel_trend_cities)

    st.markdown("---")
    st.markdown('<p class="section-header">Heatmapa cen: miasto × miesiąc</p>', unsafe_allow_html=True)
    _heatmap(sale_df)


def _price_change_chart(sale_df, sale_df_full, sel_months):
    all_months = sorted(sale_df_full["month_key"].unique())
    first_m = sel_months[0] if sel_months else all_months[0]
    last_m  = sel_months[-1] if sel_months else all_months[-1]

    first_prices = sale_df_full[sale_df_full["month_key"] == first_m].groupby("city_pl")["pricePerSqm"].median()
    last_prices  = sale_df_full[sale_df_full["month_key"] == last_m].groupby("city_pl")["pricePerSqm"].median()

    change = pd.DataFrame({"first": first_prices, "last": last_prices}).dropna()
    change["change_pct"] = (change["last"] - change["first"]) / change["first"] * 100
    change = change.reset_index().sort_values("change_pct", ascending=True)
    change = change[change["city_pl"].isin(sale_df["city_pl"].unique())]

    fig = go.Figure(go.Bar(
        y=change["city_pl"],
        x=change["change_pct"],
        orientation="h",
        marker_color=[SUCCESS if x > 0 else DANGER for x in change["change_pct"]],
        text=change["change_pct"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside",
    ))
    title = f"Zmiana ceny/m² ({MONTH_NAMES.get(first_m, first_m)} → {MONTH_NAMES.get(last_m, last_m)})"
    fig.update_layout(xaxis_title="Zmiana (%)", height=380, title=title, title_font_size=13)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _supply_chart(sale_df, sel_trend_cities):
    supply = (
        sale_df[sale_df["city_pl"].isin(sel_trend_cities[:6])]
        .groupby(["month_key", "month_label", "city_pl"])["price"]
        .count().reset_index(name="count")
    )
    supply["sort_idx"] = supply["month_key"].map(MONTH_ORDER)
    supply = supply.sort_values("sort_idx")

    fig = px.bar(
        supply, x="month_label", y="count", color="city_pl",
        barmode="stack",
        labels={"month_label": "Miesiąc", "count": "Liczba ofert", "city_pl": "Miasto"},
        title="Podaż mieszkań w czasie",
    )
    fig.update_layout(height=380, title_font_size=13)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _heatmap(sale_df):
    pivot = sale_df.groupby(["city_pl", "month_key"])["pricePerSqm"].median().unstack()
    col_labels = [MONTH_NAMES.get(m, m) for m in pivot.columns]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=col_labels,
        y=pivot.index.tolist(),
        colorscale="RdYlGn_r",
        colorbar=dict(title="zł/m²"),
        text=[[f"{v:,.0f}".replace(",", " ") for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont_size=10,
    ))
    fig.update_layout(
        title="Heatmapa mediany ceny/m² (zł) – miasto × miesiąc",
        height=500,
        title_font_size=14,
    )
    st.plotly_chart(apply_theme(fig), use_container_width=True)


# pandas is needed inside this module but imported at the top of the file above –
# add the missing import here cleanly
import pandas as pd  # noqa: E402 (kept at bottom to not clutter the top-level imports)