import streamlit as st

_CSS = """
<style>
    .stApp { background-color: #0f1117; }

    [data-testid="stSidebar"] { background-color: #161b27; }
    [data-testid="stSidebar"] .stMarkdown h2 { color: #e2e8f0; }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e2535 0%, #252d3e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.85rem !important; }
    [data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.9rem !important; }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #161b27;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        padding: 8px 20px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: #ffffff !important;
    }

    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #3b82f6;
        display: inline-block;
    }

    .info-box {
        background: linear-gradient(135deg, #1e2d4d 0%, #1a2740 100%);
        border: 1px solid #3b82f6;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        color: #cbd5e1;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }

    .city-pill {
        display: inline-block;
        background: #1e3a5f;
        color: #93c5fd;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.8rem;
        margin: 2px;
    }

    h1, h2, h3 { color: #f1f5f9; }
    p  { color: #cbd5e1; }
    hr { border-color: #2d3748; }
    
    footer {
        visibility: hidden;
    }
nag
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)
