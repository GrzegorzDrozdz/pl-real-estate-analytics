import glob
import os

import pandas as pd
import streamlit as st

from config import DATA_DIR, CITY_PL, TYPE_PL, MONTH_NAMES


def _read_monthly_csvs(pattern: str, prefix: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(DATA_DIR, pattern)))
    if not files:
        return pd.DataFrame()

    frames = []
    month_keys = list(MONTH_NAMES)

    for path in files:
        key = os.path.basename(path).replace(prefix, "").replace(".csv", "")
        df = pd.read_csv(path)
        df["month_key"]   = key
        df["month_label"] = MONTH_NAMES.get(key, key)
        df["month_order"] = month_keys.index(key) if key in month_keys else 99
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    df["pricePerSqm"] = df["price"] / df["squareMeters"]
    df["city_pl"]     = df["city"].map(CITY_PL).fillna(df["city"])
    df["type_pl"]     = df["type"].astype(str).map(TYPE_PL).fillna("Inne")
    df["rooms"]       = df["rooms"].clip(1, 6)
    return df[(df["price"] > 0) & (df["squareMeters"] > 0)]


@st.cache_data(show_spinner="Ładowanie danych rynku sprzedaży…")
def load_sale() -> pd.DataFrame:
    df = _read_monthly_csvs("apartments_pl_20*.csv", "apartments_pl_")
    if not df.empty:
        df["rooms_label"] = df["rooms"].apply(lambda x: f"{int(x)} pok." if pd.notna(x) else "?")
    return df


@st.cache_data(show_spinner="Ładowanie danych rynku najmu…")
def load_rent() -> pd.DataFrame:
    return _read_monthly_csvs("apartments_rent_pl_20*.csv", "apartments_rent_pl_")