"""Shared Plotly chart theme — call get_chart_theme(is_dark) per tab."""

PALETTE = ["#818cf8", "#06b6d4", "#34d399", "#fbbf24", "#f472b6", "#a855f7", "#38bdf8", "#f97316"]


def get_chart_theme(is_dark: bool = True) -> dict:
    if is_dark:
        return dict(
            paper_bgcolor="#09090b",
            plot_bgcolor="#09090b",
            font=dict(color="#94a3b8", family="Inter, -apple-system, sans-serif"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, showgrid=True,
                       linecolor="rgba(255,255,255,0.08)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, showgrid=True,
                       linecolor="rgba(255,255,255,0.08)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"),
                        orientation="h", y=-0.18, x=0),
            hoverlabel=dict(bgcolor="#18181b", font_color="#fafafa", bordercolor="#3f3f46"),
            margin=dict(l=8, r=8, t=44, b=8),
        )
    else:
        return dict(
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#475569", family="Inter, -apple-system, sans-serif"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.06)", zeroline=False, showgrid=True,
                       linecolor="rgba(0,0,0,0.08)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)", zeroline=False, showgrid=True,
                       linecolor="rgba(0,0,0,0.08)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#475569"),
                        orientation="h", y=-0.18, x=0),
            hoverlabel=dict(bgcolor="#f4f4f8", font_color="#09090b", bordercolor="#e4e4e7"),
            margin=dict(l=8, r=8, t=44, b=8),
        )
