"""Segments tab — adoption bar chart + parameter table."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from .charts import get_chart_theme, PALETTE


def render_segments(seg_df: pd.DataFrame, segments_raw: list,
                    is_dark: bool = True) -> None:

    CT = get_chart_theme(is_dark)
    title_color = "#e2e8f0" if is_dark else "#18181b"
    text_color  = "#e2e8f0" if is_dark else "#18181b"

    segs = pd.DataFrame(segments_raw)

    col_bar, col_rad = st.columns(2)
    with col_bar:
        if not seg_df.empty:
            fig = go.Figure([go.Bar(
                x=seg_df.segment_name,
                y=seg_df.adoption_rate,
                marker_color=PALETTE[:len(seg_df)],
                marker_line_width=0,
                text=[f"{v*100:.1f}%" for v in seg_df.adoption_rate],
                textposition="outside",
                textfont=dict(color=text_color, size=12, family="Inter"),
            )])
            fig.update_layout(
                **CT,
                title=dict(text="Final Adoption Rate by Segment", font=dict(color=title_color, size=14)),
                yaxis_tickformat=".0%", height=380, showlegend=False,
            )
            fig.update_yaxes(range=[0, max(0.15, float(seg_df.adoption_rate.max()) * 1.25)])
            st.plotly_chart(fig, use_container_width=True)

    with col_rad:
        if not segs.empty:
            traits = ["need_urgency", "tech_affinity", "social_influence",
                      "price_sensitivity", "trust_threshold", "competitor_loyalty"]
            trait_labels = ["Need", "Tech Affinity", "Social", "Price Sens.", "Trust Barrier", "Loyalty"]
            polar_bg   = "#050712" if is_dark else "#f8f8fc"
            grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)"
            fig_r = go.Figure()
            for idx, row in segs.head(4).iterrows():
                vals = [float(row[t]) for t in traits]
                fig_r.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=trait_labels + [trait_labels[0]],
                    name=row["segment_name"],
                    line=dict(color=PALETTE[idx % len(PALETTE)], width=2),
                    fill="toself",
                    opacity=0.65,
                ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor=polar_bg,
                    radialaxis=dict(visible=True, range=[0, 1], gridcolor=grid_color, tickfont=dict(size=9)),
                    angularaxis=dict(gridcolor=grid_color, tickfont=dict(color=text_color, size=10)),
                ),
                paper_bgcolor=CT["paper_bgcolor"],
                font=dict(color=text_color),
                legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.18, x=0, font=dict(size=10)),
                title=dict(text="Behavioral Vector Profile (Top 4 Segments)", font=dict(color=title_color, size=14)),
                height=380,
                margin=dict(l=28, r=28, t=48, b=36),
            )
            st.plotly_chart(fig_r, use_container_width=True)

    # ── Segment parameter table ───────────────────────────────────────────
    cols_show = ["segment_name","share","price_sensitivity","need_urgency",
                 "trust_threshold","tech_affinity","competitor_loyalty","social_influence"]
    sd = segs[cols_show].rename(columns=lambda c: c.replace("_"," ").title())
    for c in sd.columns[1:]:
        sd[c] = sd[c].apply(lambda v: f"{v:.2f}" if isinstance(v, float) else v)
    st.dataframe(sd, use_container_width=True, hide_index=True)
