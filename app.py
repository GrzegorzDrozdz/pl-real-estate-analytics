import streamlit as st
import numpy as np
import pandas as pd
import styles
import data
import sidebar
import overview
import trends
import characteristics
import spatial
import investment
import factors

st.set_page_config(
    page_title="Polski Rynek Nieruchomości",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

styles.inject()

sale_df_full = data.load_sale()
rent_df_full = data.load_rent()

ALL_CITIES = sorted(sale_df_full["city_pl"].unique()) if not sale_df_full.empty else []
ALL_MONTHS_S = sorted(sale_df_full["month_key"].unique()) if not sale_df_full.empty else []
ALL_MONTHS_R = sorted(rent_df_full["month_key"].unique()) if not rent_df_full.empty else []

filters = sidebar.render(ALL_CITIES, ALL_MONTHS_S, sale_df_full)

common_months = list(set(filters.months_sale) & set(ALL_MONTHS_R))
if not common_months:
    common_months = ALL_MONTHS_R

sale_df = sidebar.apply(sale_df_full, filters.months_sale, filters, is_rent=False)
rent_df = sidebar.apply(rent_df_full, common_months, filters, is_rent=True)

st.markdown("""
<div style="background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #1565c0 100%);
            border-radius: 16px; padding: 28px 32px; margin-bottom: 20px;
            border: 1px solid #1976d2;">
  <h1 style="color:#ffffff; margin:0; font-size:2.2rem; font-weight:800; letter-spacing:-0.5px;">
    Polski Rynek Nieruchomości 2023–2024
  </h1>
  <p style="color:#90caf9; margin:8px 0 0 0; font-size:1.05rem;">
    Interaktywny dashboard analityczny · 15 największych miast · Sprzedaż & Najem
  </p>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric("Oferty sprzedaży", f"{len(sale_df):,}".replace(",", " "))
with k2:
    avg_psqm = sale_df["pricePerSqm"].median() if not sale_df.empty else np.nan
    st.metric("Mediana ceny/m²", f"{avg_psqm:,.0f} zł".replace(",", " ") if pd.notna(avg_psqm) else "Brak")
with k3:
    avg_price = sale_df["price"].median() if not sale_df.empty else np.nan
    st.metric("Mediana ceny", f"{avg_price / 1e6:,.2f} mln zł" if pd.notna(avg_price) else "Brak")
with k4:
    avg_sqm = sale_df["squareMeters"].median() if not sale_df.empty else np.nan
    st.metric("Mediana metrażu", f"{avg_sqm:.1f} m²" if pd.notna(avg_sqm) else "Brak")
with k5:
    st.metric("Oferty najmu", f"{len(rent_df):,}".replace(",", " "))
with k6:
    avg_rent = rent_df["pricePerSqm"].median() if not rent_df.empty else np.nan
    display_rent = f"{avg_rent:.1f} zł" if pd.notna(avg_rent) else "Brak"
    st.metric("Mediana czynszu/m²", display_rent)

st.markdown("---")

tabs = st.tabs([
    "Przegląd rynku",
    "Trendy cenowe",
    "Charakterystyka ofert",
    "Analiza przestrzenna",
    "Sprzedaż vs Najem",
    "Czynniki cenowe",
])

with tabs[0]:
    overview.render(sale_df)

with tabs[1]:
    trends.render(sale_df, sale_df_full, filters.months_sale, ALL_CITIES)

with tabs[2]:
    characteristics.render(sale_df, filters.cities)

with tabs[3]:
    spatial.render(sale_df, filters.cities, ALL_CITIES)

with tabs[4]:
    investment.render(sale_df_full, rent_df_full, sale_df, rent_df)

with tabs[5]:
    factors.render(sale_df, filters.cities)
