import plotly.express as px

# ── Kolory interfejsu ────────────────────────────────────────────────────────

PLOTLY_THEME = "plotly_dark"
CITY_COLORS  = px.colors.qualitative.Plotly

PRIMARY   = "#3b82f6"
SECONDARY = "#6366f1"
SUCCESS   = "#22c55e"
WARNING   = "#f59e0b"
DANGER    = "#ef4444"

PLOT_BG   = "#161b27"
PAPER_BG  = "#0f1117"
GRID_COLOR = "#2d3748"
TEXT_COLOR = "#94a3b8"

# ── Ścieżka danych ───────────────────────────────────────────────────────────

DATA_DIR = "dane"

# ── Słowniki tłumaczeń ───────────────────────────────────────────────────────

CITY_PL = {
    "warszawa":   "Warszawa",
    "krakow":     "Kraków",
    "wroclaw":    "Wrocław",
    "poznan":     "Poznań",
    "gdansk":     "Gdańsk",
    "gdynia":     "Gdynia",
    "szczecin":   "Szczecin",
    "lodz":       "Łódź",
    "lublin":     "Lublin",
    "bialystok":  "Białystok",
    "katowice":   "Katowice",
    "rzeszow":    "Rzeszów",
    "bydgoszcz":  "Bydgoszcz",
    "radom":      "Radom",
    "czestochowa":"Częstochowa",
}

TYPE_PL = {
    "blockOfFlats":      "Blok",
    "tenement":          "Kamienica",
    "apartmentBuilding": "Apartamentowiec",
    "nan":               "Inne",
}

MONTH_NAMES = {
    "2023_08": "Sie'23",
    "2023_09": "Wrz'23",
    "2023_10": "Paź'23",
    "2023_11": "Lis'23",
    "2023_12": "Gru'23",
    "2024_01": "Sty'24",
    "2024_02": "Lut'24",
    "2024_03": "Mar'24",
    "2024_04": "Kwi'24",
    "2024_05": "Maj'24",
    "2024_06": "Cze'24",
}

MONTH_ORDER = {k: i for i, k in enumerate(MONTH_NAMES)}
