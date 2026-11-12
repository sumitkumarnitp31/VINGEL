import streamlit as st
import pandas as pd
from components.landing import render_landing
from components.charts import get_chart_theme, PALETTE
from components.tab_graph import render_graph_preview
import plotly.graph_objects as go
import os

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")

result = st.session_state.get("result")
if not result:
    render_landing(BACKEND)
    st.stop()

is_dark     = st.session_state.get("theme", "dark") == "dark"
title_color = "#e2e8f0" if is_dark else "#18181b"
text_color  = "#e2e8f0" if is_dark else "#18181b"

seg_df  = pd.DataFrame(result.get("segment_adoption", []))
base_df = pd.DataFrame(result.get("base_monthly", []))
p10_df  = pd.DataFrame(result.get("mc_p10", []))
p50_df  = pd.DataFrame(result.get("mc_p50", []))
p90_df  = pd.DataFrame(result.get("mc_p90", []))
assum   = result["assumptions"]

# ── Automated Research Brief (derived from simulation outputs) ────────────────
p10_mrr = float(p10_df["mrr"].iloc[-1]) if not p10_df.empty else 0.0
p50_mrr = float(p50_df["mrr"].iloc[-1]) if not p50_df.empty else 0.0
p90_mrr = float(p90_df["mrr"].iloc[-1]) if not p90_df.empty else 0.0
spread_ratio = (p90_mrr / p10_mrr) if p10_mrr > 0 else 0.0
cum_rev = float(base_df["cumulative_revenue"].iloc[-1]) if not base_df.empty else 0.0
end_cust = int(base_df["total_customers"].iloc[-1]) if not base_df.empty else 0

if not seg_df.empty and {"segment_name", "adoption_rate"}.issubset(seg_df.columns):
    top_row = seg_df.sort_values("adoption_rate", ascending=False).iloc[0]
    top_seg = str(top_row["segment_name"])
    top_rate = f"{float(top_row['adoption_rate']) * 100:.1f}% adoption"
else:
    top_seg, top_rate = "—", "No segments"

st.markdown(
    '<div class="vg-section-head">🔬 Executive Simulation Summary</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
<div class="vg-insight-grid">
  <div class="vg-insight-card" style="border-left-color:#818cf8">
    <div class="vg-insight-lbl">P10–P90 MRR Envelope</div>
    <div class="vg-insight-val">${p10_mrr:,.0f} – ${p90_mrr:,.0f}</div>
    <div class="vg-insight-note">Median P50: ${p50_mrr:,.0f} ({spread_ratio:.2f}× spread)</div>
  </div>
  <div class="vg-insight-card" style="border-left-color:#34d399">
    <div class="vg-insight-lbl">Highest-Converting Segment</div>
    <div class="vg-insight-val">{top_seg}</div>
    <div class="vg-insight-note">{top_rate} at horizon end</div>
  </div>
  <div class="vg-insight-card" style="border-left-color:#06b6d4">
    <div class="vg-insight-lbl">Cumulative Base Revenue</div>
    <div class="vg-insight-val">${cum_rev:,.0f}</div>
    <div class="vg-insight-note">{end_cust:,} active paying customers</div>
  </div>
  <div class="vg-insight-card" style="border-left-color:#fbbf24">
    <div class="vg-insight-lbl">Viral &amp; Retention Balance</div>
    <div class="vg-insight-val">{assum['virality_coefficient']:.2f}× virality</div>
    <div class="vg-insight-note">{assum['churn_rate_monthly']*100:.1f}% base monthly churn · {assum['switching_cost']*100:.0f}% switching friction</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Two-column core charts ────────────────────────────────────────────────────
CT = get_chart_theme(is_dark)
col_left, col_right = st.columns(2)

with col_left:
    if not seg_df.empty and {"segment_name", "adoption_rate"}.issubset(seg_df.columns):
        sdf = seg_df.sort_values("adoption_rate", ascending=True)
        fig_seg = go.Figure(go.Bar(
            y=sdf["segment_name"],
            x=(sdf["adoption_rate"] * 100).round(1),
            orientation="h",
            marker_color=PALETTE[: len(sdf)],
            text=(sdf["adoption_rate"] * 100).round(1).astype(str) + "%",
            textposition="outside",
            textfont=dict(color=text_color, size=11),
        ))
        fig_seg.update_layout(
            **CT,
            title=dict(text="Adoption Rate by Customer Segment", font=dict(color=title_color, size=14)),
            xaxis_title="Adoption %",
            height=340,
            showlegend=False,
        )
        fig_seg.update_xaxes(range=[0, max(15.0, float((sdf["adoption_rate"] * 100).max()) * 1.22)])
        st.plotly_chart(fig_seg, use_container_width=True)

with col_right:
    if not base_df.empty and not p10_df.empty and not p90_df.empty:
        fig_mrr = go.Figure()
        fig_mrr.add_trace(go.Scatter(
            x=p90_df["month"], y=p90_df["mrr"],
            fill=None, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig_mrr.add_trace(go.Scatter(
            x=p10_df["month"], y=p10_df["mrr"],
            fill="tonexty", mode="lines", line=dict(width=0),
            fillcolor="rgba(129,140,248,0.16)", name="P10–P90 band",
        ))
        fig_mrr.add_trace(go.Scatter(
            x=p50_df["month"], y=p50_df["mrr"],
            mode="lines", line=dict(color="#818cf8", width=1.8, dash="dot"), name="P50 median",
        ))
        fig_mrr.add_trace(go.Scatter(
            x=base_df["month"], y=base_df["mrr"],
            mode="lines", line=dict(color="#34d399", width=2.5), name="Base scenario",
        ))
        fig_mrr.update_layout(
            **CT,
            title=dict(text="MRR Trajectory & Monte Carlo Envelope", font=dict(color=title_color, size=14)),
            xaxis_title="Month", yaxis_title="MRR ($)", hovermode="x unified", height=340,
        )
        st.plotly_chart(fig_mrr, use_container_width=True)

# ── AI assumptions summary ────────────────────────────────────────────────────
with st.expander("🤖 Prior Assumptions & Product Parameters"):
    a1, a2, a3, a4, a5, a6 = st.columns(6)
    a1.metric("TAM",           f"{assum['total_addressable_market']:,}")
    a2.metric("Problem Need",  f"{assum['problem_severity']*100:.0f}%")
    a3.metric("Feature Match", f"{assum['feature_match']*100:.0f}%")
    a4.metric("Virality",      f"{assum['virality_coefficient']:.2f}×")
    a5.metric("Mktg Reach",    f"{assum['monthly_marketing_reach']*100:.1f}%")
    a6.metric("Monthly Churn", f"{assum['churn_rate_monthly']*100:.1f}%")

st.markdown("<div style='margin:.75rem 0'></div>", unsafe_allow_html=True)

# ── Live population graph ─────────────────────────────────────────────────────
st.markdown(
    '<div class="vg-section-head">🌐 Population Graph Topology</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="vg-result-sub">Force-directed segment &amp; agent clusters — hover any node for behavioral state. '
    'Open the <b>Graph</b> page in the sidebar for full-screen controls and breakdown.</div>',
    unsafe_allow_html=True,
)

gd = st.session_state.get("graph_data", {})
render_graph_preview(gd, is_dark, result=result)
