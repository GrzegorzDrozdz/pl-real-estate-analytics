from dataclasses import dataclass

import numpy as np
import streamlit as st

from config import MONTH_NAMES


@dataclass
class Filters:
    cities: list[str]
    months_sale: list[str]
    building_types: list[str]
    room_range: tuple[int, int]
    ppsqm_range: tuple[int, int]
    sqm_range: tuple[int, int]


def render(all_cities: list[str], all_months_sale: list[str], sale_df_full) -> Filters:
    with st.sidebar:
        st.markdown("## 🏠 Panel Filtrów")
        st.markdown("---")

        # ── Miasta ──────────────────────────────────────────────────────────
        st.markdown("### 🏙️ Miasta")
        if st.checkbox("Wszystkie miasta", value=True):
            cities = all_cities
        else:
            default = ["Warszawa", "Kraków", "Wrocław", "Gdańsk", "Poznań"]
            cities = st.multiselect(
                "Wybierz miasta",
                options=all_cities,
                default=[c for c in default if c in all_cities] or all_cities,
            ) or all_cities

        # ── Okres ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📅 Okres (sprzedaż)")

        if all_months_sale:
            labels = [MONTH_NAMES.get(k, k) for k in all_months_sale]
            lo, hi = st.select_slider(
                "Zakres miesięcy",
                options=labels,
                value=(labels[0], labels[-1]),
                key="sale_range",
            )
            i0, i1 = labels.index(lo), labels.index(hi)
            months_sale = all_months_sale[i0 : i1 + 1]
        else:
            months_sale = []

        # ── Typ budynku ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🏗️ Typ budynku")
        all_types = ["Blok", "Kamienica", "Apartamentowiec", "Inne"]
        building_types = st.multiselect("Typ", options=all_types, default=all_types) or all_types

        # ── Pokoje ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🚪 Liczba pokoi")
        room_range = st.slider("Pokoje", min_value=1, max_value=6, value=(1, 6))

        # ── Cena/m² ──────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 💰 Cena (zł/m²)")
        ppsqm_max = (
            int(sale_df_full["pricePerSqm"].quantile(0.99))
            if not sale_df_full.empty
            else 30_000
        )
        ppsqm_range = st.slider(
            "Cena za m²",
            min_value=2_000,
            max_value=ppsqm_max,
            value=(2_000, ppsqm_max),
            step=500,
            format="%d zł",
        )

        # ── Metraż ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📐 Metraż (m²)")
        sqm_range = st.slider("Metraż", min_value=20, max_value=150, value=(20, 150), step=5)

        st.markdown("---")
        st.caption("📊 Dane: Otodom Analytics\n🗓️ Okres: VIII 2023 – VI 2024\n🏙️ 15 największych miast Polski")

    return Filters(
        cities=cities,
        months_sale=months_sale,
        building_types=building_types,
        room_range=room_range,
        ppsqm_range=ppsqm_range,
        sqm_range=sqm_range,
    )


def apply(df, months: list[str], filters: Filters, is_rent: bool = False):
    if df.empty:
        return df

    p_min, p_max = (0, 1_000) if is_rent else filters.ppsqm_range

    mask = (
        df["city_pl"].isin(filters.cities)
        & df["month_key"].isin(months)
        & df["type_pl"].isin(filters.building_types)
        & df["rooms"].between(*filters.room_range)
        & df["pricePerSqm"].between(p_min, p_max)
        & df["squareMeters"].between(*filters.sqm_range)
    )
    return df[mask].copy()