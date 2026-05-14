import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from charts import apply_theme
from config import CITY_COLORS, SUCCESS, DANGER

_SQM_BINS   = [20, 30, 40, 50, 60, 70, 80, 100, 120, 150]
_SQM_LABELS = ["20–30","30–40","40–50","50–60","60–70","70–80","80–100","100–120","120–150"]

_PRICE_BINS   = [0, 300, 400, 500, 600, 800, 1000, 1500, 2500]
_PRICE_LABELS = ["<300","300–400","400–500","500–600","600–800","800–1000","1000–1500",">1500"]

_AMENITIES = {
    "hasParkingSpace": "Miejsce parkingowe",
    "hasBalcony":      "Balkon",
    "hasElevator":     "Winda",
    "hasSecurity":     "Ochrona",
    "hasStorageRoom":  "Komórka lokal.",
}


def render(sale_df, sel_cities: list[str]):
    if sale_df.empty:
        st.warning("Brak danych sprzedaży dla wybranych filtrów.")
        return

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown('<p class="section-header">Rozkład typów budynków</p>', unsafe_allow_html=True)
        _building_types_pie(sale_df)

    with col_c2:
        st.markdown('<p class="section-header">Rozkład liczby pokoi</p>', unsafe_allow_html=True)
        _rooms_bar(sale_df)

    st.markdown("---")
    col_c3, col_c4 = st.columns(2)

    with col_c3:
        st.markdown('<p class="section-header">Cena/m² według liczby pokoi i miasta</p>', unsafe_allow_html=True)
        _rooms_by_city(sale_df, sel_cities)

    with col_c4:
        st.markdown('<p class="section-header">Wpływ udogodnień na cenę</p>', unsafe_allow_html=True)
        _amenities_chart(sale_df)

    st.markdown("---")
    st.markdown('<p class="section-header">Rozkład metrażu i ceny całkowitej</p>', unsafe_allow_html=True)
    col_c5, col_c6 = st.columns(2)

    with col_c5:
        _sqm_distribution(sale_df)

    with col_c6:
        _price_distribution(sale_df)

    st.markdown("---")
    st.markdown('<p class="section-header">Wiek budynków a cena</p>', unsafe_allow_html=True)
    _build_era_chart(sale_df)


def _building_types_pie(sale_df):
    dist = sale_df["type_pl"].value_counts().reset_index()
    dist.columns = ["Typ", "Liczba"]
    fig = px.pie(
        dist, values="Liczba", names="Typ",
        color_discrete_sequence=CITY_COLORS,
        hole=0.45,
        title="Struktura typów budynków",
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(height=380, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _rooms_bar(sale_df):
    dist = sale_df["rooms"].value_counts().sort_index().reset_index()
    dist.columns = ["Pokoje", "Liczba"]
    dist["Pokoje"] = dist["Pokoje"].apply(lambda x: f"{int(x)} pok.")
    fig = px.bar(
        dist, x="Pokoje", y="Liczba",
        color="Liczba", color_continuous_scale="Blues",
        text="Liczba",
        title="Rozkład liczby pokoi",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=380, coloraxis_showscale=False, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _rooms_by_city(sale_df, sel_cities):
    room_city = (
        sale_df.groupby(["city_pl", "rooms"])["pricePerSqm"]
        .median().reset_index()
    )
    room_city["rooms"] = room_city["rooms"].apply(lambda x: f"{int(x)} pok.")

    fig = px.bar(
        room_city[room_city["city_pl"].isin(sel_cities[:8])],
        x="city_pl", y="pricePerSqm", color="rooms",
        barmode="group",
        labels={"city_pl": "Miasto", "pricePerSqm": "Mediana ceny/m² (zł)", "rooms": "Pokoje"},
        title="Mediana ceny/m² wg liczby pokoi",
    )
    fig.update_layout(height=420, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _amenities_chart(sale_df):
    rows = []
    for col, label in _AMENITIES.items():
        if col not in sale_df.columns:
            continue
        grp = sale_df.groupby(col)["pricePerSqm"].median()
        if "yes" in grp.index and "no" in grp.index:
            diff_pct = (grp["yes"] - grp["no"]) / grp["no"] * 100
            rows.append({"Udogodnienie": label, "Różnica %": diff_pct})

    if not rows:
        return

    df = pd.DataFrame(rows).sort_values("Różnica %", ascending=True)
    fig = go.Figure(go.Bar(
        y=df["Udogodnienie"],
        x=df["Różnica %"],
        orientation="h",
        marker_color=[SUCCESS if x > 0 else DANGER for x in df["Różnica %"]],
        text=df["Różnica %"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Premia cenowa za udogodnienia (%)",
        xaxis_title="Różnica w medianie ceny/m² (%)",
        height=380,
        title_font_size=14,
    )
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _sqm_distribution(sale_df):
    df = sale_df.copy()
    df["sqm_bucket"] = pd.cut(df["squareMeters"], bins=_SQM_BINS, labels=_SQM_LABELS)
    dist = df["sqm_bucket"].value_counts().sort_index().reset_index()
    dist.columns = ["Metraż (m²)", "Liczba"]

    fig = px.bar(
        dist, x="Metraż (m²)", y="Liczba",
        color="Liczba", color_continuous_scale="Purples",
        text="Liczba",
        title="Rozkład metrażu mieszkań",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=380, coloraxis_showscale=False, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _price_distribution(sale_df):
    df = sale_df.copy()
    df["price_bucket"] = pd.cut(df["price"] / 1000, bins=_PRICE_BINS, labels=_PRICE_LABELS)
    dist = df["price_bucket"].value_counts().sort_index().reset_index()
    dist.columns = ["Cena (tys. zł)", "Liczba"]

    fig = px.bar(
        dist, x="Cena (tys. zł)", y="Liczba",
        color="Liczba", color_continuous_scale="Oranges",
        text="Liczba",
        title="Rozkład cen mieszkań (tys. zł)",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=380, coloraxis_showscale=False, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)


def _build_era_chart(sale_df):
    df = sale_df.dropna(subset=["buildYear"]).copy()
    df = df[(df["buildYear"] >= 1900) & (df["buildYear"] <= 2025)]
    df["era"] = pd.cut(
        df["buildYear"],
        bins=[1899, 1939, 1959, 1979, 1999, 2009, 2019, 2025],
        labels=["Do 1939", "1940–1959", "1960–1979", "1980–1999", "2000–2009", "2010–2019", "2020+"],
    )
    era_stats = df.groupby("era", observed=True)["pricePerSqm"].median().reset_index()
    era_stats.columns = ["Era budowy", "Mediana ceny/m²"]

    fig = px.bar(
        era_stats, x="Era budowy", y="Mediana ceny/m²",
        color="Mediana ceny/m²", color_continuous_scale="Turbo",
        text=era_stats["Mediana ceny/m²"].apply(
            lambda x: f"{x:,.0f}".replace(",", " ") if pd.notna(x) else ""
        ),
        title="Mediana ceny/m² według epoki budowy",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=380, coloraxis_showscale=False, title_font_size=14)
    st.plotly_chart(apply_theme(fig), use_container_width=True)