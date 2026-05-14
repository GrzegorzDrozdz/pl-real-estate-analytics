import plotly.graph_objects as go

from config import PAPER_BG, PLOT_BG, GRID_COLOR, TEXT_COLOR


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent dark theme to every Plotly figure."""
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_COLOR, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID_COLOR),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig