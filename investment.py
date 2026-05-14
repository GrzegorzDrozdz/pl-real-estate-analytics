import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import MONTH_NAMES

def render(sale_df_full, rent_df_full, sale_df, rent_df):
    if sale_df_full.empty or rent_df_full.empty:
        st.warning("⚠️ Brak dostępnych danych z rynków sprzedaży lub wynajmu do zestawienia parametrów inwestycyjnych.")
        return

    common_months = sorted(set(sale_df["month_key"].unique()) & set(rent_df["month_key"].unique()))
    common_cities = sorted(set(sale_df["city_pl"].unique()) & set(rent_df["city_pl"].unique()))

    if not common_cities:
        st.warning("⚠️ Brak wspólnych miast w obu zbiorach danych dla wybranych filtrów.")
        return

    st.markdown('<h3 style="color: #3b82f6;">Porównanie: Cena zakupu vs Czynsz miesięczny</h3>', unsafe_allow_html=True)

    sale_city_m = (
        sale_df[sale_df["city_pl"].isin(common_cities)]
        .groupby("city_pl")
        .agg(med_sale_psqm=("pricePerSqm", "median"), med_sale_price=("price", "median"))
        .reset_index()
    )
    rent_city_m = (
        rent_df[rent_df["city_pl"].isin(common_cities)]
        .groupby("city_pl")
        .agg(med_rent_psqm=("pricePerSqm", "median"), med_rent=("price", "median"))
        .reset_index()
    )
    combined = sale_city_m.merge(rent_city_m, on="city_pl")
    combined["gross_yield"] = (combined["med_rent"] * 12) / combined["med_sale_price"] * 100
    combined["payback_years"] = combined["med_sale_price"] / (combined["med_rent"] * 12)

    col_rv1, col_rv2 = st.columns(2)

    with col_rv1:
        df_yield = combined.sort_values("gross_yield", ascending=True)
        fig_yield = px.bar(
            df_yield,
            x="gross_yield", y="city_pl",
            orientation="h",
            color="gross_yield",
            color_continuous_scale="RdYlGn",
            text=df_yield["gross_yield"].apply(lambda x: f"{x:.2f}%"),
            labels={"city_pl": "Miasto", "gross_yield": "Stopa zwrotu brutto (%)"},
            title="Brutto stopa zwrotu z najmu (%)",
        )
        fig_yield.update_traces(textposition="outside")
        fig_yield.update_layout(height=480, coloraxis_showscale=False, title_font_size=14)
        st.plotly_chart(apply_theme(fig_yield), use_container_width=True)

    with col_rv2:
        df_payback = combined.sort_values("payback_years", ascending=False)
        fig_payback = px.bar(
            df_payback,
            x="payback_years", y="city_pl",
            orientation="h",
            color="payback_years",
            color_continuous_scale="RdYlGn_r",
            text=df_payback["payback_years"].apply(lambda x: f"{x:.0f} lat"),
            labels={"city_pl": "Miasto", "payback_years": "Okres zwrotu (lata)"},
            title="Okres zwrotu z inwestycji (lata)",
        )
        fig_payback.update_traces(textposition="outside")
        fig_payback.update_layout(height=480, coloraxis_showscale=False, title_font_size=14)
        st.plotly_chart(apply_theme(fig_payback), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="color: #3b82f6;">Trendy czynszów miesięcznych</h3>', unsafe_allow_html=True)

    rent_trend = (
        rent_df[rent_df["city_pl"].isin(common_cities)]
        .groupby(["month_key", "month_label", "city_pl"])["pricePerSqm"]
        .median().reset_index()
    )

    month_order_map2 = {k: i for i, k in enumerate(MONTH_NAMES.keys())}
    rent_trend["sort_idx"] = rent_trend["month_key"].map(month_order_map2)
    rent_trend = rent_trend.sort_values("sort_idx")

    default_cities = common_cities[:6] if len(common_cities) >= 6 else common_cities
    sel_rent_cities = st.multiselect(
        "Wybierz miasta (najem):",
        options=common_cities,
        default=default_cities,
        key="rent_cities",
    )
    if not sel_rent_cities:
        sel_rent_cities = default_cities

    fig_rent_trend = px.line(
        rent_trend[rent_trend["city_pl"].isin(sel_rent_cities)],
        x="month_label", y="pricePerSqm",
        color="city_pl", markers=True,
        labels={"month_label": "Miesiąc", "pricePerSqm": "Mediana czynszu/m² (zł)", "city_pl": "Miasto"},
        title="Trend mediany czynszu/m² w czasie",
    )
    fig_rent_trend.update_traces(line_width=2.5, marker_size=8)
    fig_rent_trend.update_layout(height=380, title_font_size=14)
    st.plotly_chart(apply_theme(fig_rent_trend), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="color: #3b82f6;">Macierz porównawcza: zakup vs najem</h3>', unsafe_allow_html=True)

    fig_bubble = px.scatter(
        combined,
        x="med_sale_psqm", y="med_rent_psqm",
        size="gross_yield", color="payback_years",
        text="city_pl",
        color_continuous_scale="RdYlGn_r",
        size_max=40,
        labels={
            "med_sale_psqm": "Mediana ceny sprzedaży/m² (zł)",
            "med_rent_psqm": "Mediana czynszu/m² (zł)",
            "gross_yield": "Stopa zwrotu (%)",
            "payback_years": "Okres zwrotu (lata)",
        },
        title="Cena zakupu vs Czynsz (rozmiar = stopa zwrotu, kolor = okres zwrotu)",
    )
    fig_bubble.update_traces(textposition="top center", textfont_size=11)
    fig_bubble.update_layout(height=500, title_font_size=14)
    st.plotly_chart(apply_theme(fig_bubble), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="color: #3b82f6;">Tabela inwestycyjna</h3>', unsafe_allow_html=True)

    display_combined = combined.sort_values("gross_yield", ascending=False).copy()
    display_combined["med_sale_price"] = display_combined["med_sale_price"].apply(lambda x: f"{x / 1000:,.0f} tys. zł".replace(",", " "))
    display_combined["med_sale_psqm"] = display_combined["med_sale_psqm"].apply(lambda x: f"{x:,.0f} zł/m²".replace(",", " "))
    display_combined["med_rent"] = display_combined["med_rent"].apply(lambda x: f"{x:,.0f} zł/mies.".replace(",", " "))
    display_combined["med_rent_psqm"] = display_combined["med_rent_psqm"].apply(lambda x: f"{x:.1f} zł/m²")
    display_combined["gross_yield"] = display_combined["gross_yield"].apply(lambda x: f"{x:.2f}%")
    display_combined["payback_years"] = display_combined["payback_years"].apply(lambda x: f"{x:.0f} lat")

    display_combined = display_combined.rename(columns={
        "city_pl": "Miasto",
        "med_sale_price": "Mediana ceny",
        "med_sale_psqm": "Cena/m²",
        "med_rent": "Czynsz/mies.",
        "med_rent_psqm": "Czynsz/m²",
        "gross_yield": "Stopa zwrotu brutto",
        "payback_years": "Okres zwrotu"
    })

    kolumny_tab = ["Miasto", "Mediana ceny", "Cena/m²", "Czynsz/mies.", "Czynsz/m²", "Stopa zwrotu brutto", "Okres zwrotu"]
    st.dataframe(display_combined[kolumny_tab].reset_index(drop=True), use_container_width=True, height=420)