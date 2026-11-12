"""Landing page — hero, feature cards, CTA. Pure Streamlit components."""
import streamlit as st
import requests


_CARDS = [
    ("🤖", "Gemini AI Analysis",
     "Gemini AI generates TAM, churn, virality and tailored "
     "customer segments specific to your product and market."),
    ("⚡", "Vectorized Engine",
     "Synthetic users · adoption funnel · pure NumPy — "
     "results in seconds, not minutes."),
    ("📊", "Monte Carlo Bands",
     "Parameter-varied runs yield P10 / P50 / P90 revenue envelopes "
     "so you see the full distribution of outcomes."),
    ("🌐", "Population Graph",
     "Explore customer segments and adoption states interactively "
     "via Neo4j graph visualization."),
]

_STATS = [
    ("10k+",  "Synthetic Users"),
    ("20×+",  "Monte Carlo Runs"),
    ("4–8",   "Customer Segments"),
    ("<10s",  "Quick Demo"),
]


def render_landing(backend_url: str) -> None:
    st.markdown(
        '<div class="vg-badge">'
        '<span class="vg-badge-dot"></span>'
        'Gemini AI &nbsp;·&nbsp; Monte Carlo &nbsp;·&nbsp; Vectorized NumPy'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vg-title">VINGEL Market Simulator</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vg-sub">'
        'Turn any product idea into a data-driven market forecast — '
        'AI-generated assumptions, adoption curves, revenue uncertainty bands, '
        'and on-chain proof of your analysis, in under 30 seconds.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Stats row
    stat_cols = st.columns(len(_STATS))
    for col, (num, lbl) in zip(stat_cols, _STATS):
        col.markdown(
            f'<div class="vg-stat-item">'
            f'<span class="vg-stat-num">{num}</span>'
            f'<span class="vg-stat-lbl">{lbl}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin:1.5rem 0'></div>", unsafe_allow_html=True)

    # Feature cards
    card_cols = st.columns(len(_CARDS))
    for col, (icon, title, desc) in zip(card_cols, _CARDS):
        col.markdown(
            f'<div class="vg-card">'
            f'<span class="vg-card-icon">{icon}</span>'
            f'<div class="vg-card-title">{title}</div>'
            f'<div class="vg-card-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)

    col_demo, col_reset, *_ = st.columns([1, 1, 1, 1, 1])

    with col_demo:
        if st.button("⚡  Quick Demo", use_container_width=True, type="primary"):
            _run_demo(backend_url)

    with col_reset:
        if st.button("🗑️  Reset", use_container_width=True):
            for k in ["result", "prefill", "prefill_config", "payload", "graph_data"]:
                st.session_state.pop(k, None)
            st.rerun()


def _run_demo(backend_url: str) -> None:
    backend_url = backend_url.rstrip("/")
    with st.spinner("Simulating market dynamics (first request on free tier may take ~30s to wake server)…"):
        try:
            r  = requests.get(f"{backend_url}/api/demo",       timeout=120)
            ri = requests.get(f"{backend_url}/api/demo-input", timeout=30)
            r.raise_for_status()
            di = ri.json()
            st.session_state.update({
                "result":         r.json(),
                "prefill":        di["product"],
                "prefill_config": di["config"],
                "payload":        di,
            })
            try:
                gd = requests.get(
                    f"{backend_url}/api/graph/nodes",
                    params={"product": r.json().get("product_name", "ProjectFlow Pro"), "limit": 50},
                    timeout=10,
                )
                st.session_state["graph_data"] = gd.json() if gd.ok else {"source": "unavailable"}
            except Exception:
                st.session_state["graph_data"] = {"source": "unavailable"}
            st.rerun()
        except requests.exceptions.ConnectionError:
            st.error("Backend not running — open a terminal and run: `./run.sh backend`")
        except Exception as e:
            st.error(str(e))
