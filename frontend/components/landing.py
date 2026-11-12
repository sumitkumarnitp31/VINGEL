"""Landing page — research hero, live telemetry, benchmark presets, methodology."""
import streamlit as st
import requests


_CARDS = [
    ("🧠", "LLM Market Priors",
     "Gemini AI estimates TAM, switching friction, virality, and heterogeneous "
     "customer segment priors — with deterministic heuristic fallback."),
    ("⚡", "Vectorized Agent Engine",
     "Pure NumPy vectorized state machine simulates Unaware → Aware → Active → Churned "
     "transitions across synthetic populations in milliseconds."),
    ("📊", "Stochastic Monte Carlo",
     "Perturbs market parameters across N stochastic trials to produce calibrated "
     "P10 / P50 / P90 revenue and adoption confidence envelopes."),
    ("🌐", "Population Topology",
     "Interactive force-directed segment and agent graph visualizing adoption clusters, "
     "churn pressure, and trust thresholds."),
]

_STATS = [
    ("10k–100k", "Synthetic Agents"),
    ("20–500×",  "Monte Carlo Trials"),
    ("4–8",      "Behavioral Segments"),
    ("P10/50/90","Confidence Bands"),
]

_PRESETS = {
    "enterprise_ai": {
        "label": "🧠 AI DevTool (Enterprise)",
        "product": {
            "product_name": "CodePilot Enterprise",
            "product_description": "Autonomous code-review and vulnerability remediation agent integrated into GitHub Enterprise and Azure DevOps.",
            "target_market": "Mid-to-large engineering organizations (100–2,000 devs)",
            "price": 129.0,
            "billing_model": "monthly_subscription",
            "geography": ["US", "UK", "Germany", "India"],
            "competitors": ["GitHub Copilot", "SonarQube", "Snyk"],
            "channels": ["Enterprise Sales", "Developer Advocacy", "Security Benchmarks"],
            "features": ["PR security synthesis", "Repo-scale AST analysis", "SOC2 audit trails", "Self-hosted runner"],
        },
        "config": {"n_users": 10_000, "n_months": 18, "n_monte_carlo": 20, "random_seed": 42},
    },
    "consumer_plg": {
        "label": "📱 Consumer PLG (Freemium)",
        "product": {
            "product_name": "PulseFit AI",
            "product_description": "Adaptive biometric workout and recovery coach using wearable telemetry with social accountability loops.",
            "target_market": "Health-conscious consumers & wearable users, ages 20–45",
            "price": 14.0,
            "billing_model": "freemium",
            "geography": ["US", "Canada", "UK", "Australia"],
            "competitors": ["Whoop", "Strava", "Fitbod"],
            "channels": ["TikTok Creators", "Referral Loops", "App Store SEO"],
            "features": ["HRV recovery scoring", "Voice workout cues", "Friend challenges", "Apple Watch sync"],
        },
        "config": {"n_users": 10_000, "n_months": 18, "n_monte_carlo": 20, "random_seed": 7},
    },
}


def _fetch_health(backend_url: str) -> dict | None:
    cached = st.session_state.get("_health_cache")
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{backend_url.rstrip('/')}/health", timeout=2.5)
        if r.ok:
            data = r.json()
            st.session_state["_health_cache"] = data
            return data
    except Exception:
        pass
    return None


def render_landing(backend_url: str) -> None:
    backend_url = backend_url.rstrip("/")

    # Live backend telemetry pill
    health = _fetch_health(backend_url)
    if health:
        ai_mode = health.get("ai_mode", "heuristic")
        py_ver = (health.get("python", "") or "").split(" ")[0]
        st.markdown(
            f'<div class="vg-status-bar">'
            f'<span class="vg-status-ok">● API Online</span>'
            f'<span class="vg-status-sep">|</span>'
            f'<span>Prior Engine: <b>{ai_mode}</b></span>'
            f'<span class="vg-status-sep">|</span>'
            f'<span>Version: <b>v{health.get("version", "0.5.0")}</b></span>'
            f'<span class="vg-status-sep">|</span>'
            f'<span>Runtime: <b>Python {py_ver}</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="vg-status-bar">'
            '<span class="vg-status-warn">● Backend Standby / Waking</span>'
            '<span class="vg-status-sep">|</span>'
            '<span>Click any benchmark below to wake &amp; run simulation</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="vg-badge">'
        '<span class="vg-badge-dot"></span>'
        'Agent-Based Market Simulation &nbsp;·&nbsp; Stochastic Monte Carlo &nbsp;·&nbsp; Gemini AI'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vg-title">VINGEL Market Simulator</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vg-sub">'
        'Simulate emergent product adoption across heterogeneous synthetic populations. '
        'Combines LLM-estimated market priors with vectorized discrete-time agent dynamics '
        'and Monte Carlo uncertainty quantification.'
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

    st.markdown("<div style='margin:1.35rem 0'></div>", unsafe_allow_html=True)

    # Action / Benchmark Presets Row
    st.markdown('<div class="sb-sec">Interactive Benchmarks</div>', unsafe_allow_html=True)
    c_demo, c_ent, c_plg, c_reset = st.columns([1.2, 1.4, 1.4, 0.8])

    with c_demo:
        if st.button("⚡  Quick Demo (B2B SaaS)", use_container_width=True, type="primary"):
            _run_demo(backend_url)

    with c_ent:
        if st.button(_PRESETS["enterprise_ai"]["label"], use_container_width=True):
            _run_preset(backend_url, _PRESETS["enterprise_ai"])

    with c_plg:
        if st.button(_PRESETS["consumer_plg"]["label"], use_container_width=True):
            _run_preset(backend_url, _PRESETS["consumer_plg"])

    with c_reset:
        if st.button("🗑️  Reset", use_container_width=True):
            for k in ["result", "prefill", "prefill_config", "payload", "graph_data", "_health_cache"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)

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

    st.markdown("<div style='margin:1.25rem 0'></div>", unsafe_allow_html=True)

    # Research Methodology & Mathematical Model
    with st.expander("📐  Mathematical Model & Agent Dynamics", expanded=False):
        st.markdown(
            """
<div class="vg-eq-grid">
  <div class="vg-eq-card">
    <div class="vg-eq-title">1 · Heterogeneous Agent Sampling</div>
    <div class="vg-eq-formula">x_i ~ clip(N(μ_s, 0.12²), 0, 1) &nbsp;|&nbsp; θ_buy ~ Beta(2.5, 2.5)</div>
    <div class="vg-eq-desc">Each synthetic agent inherits segment-level behavioral means (price sensitivity, need urgency, trust, loyalty) perturbed individually, plus Beta-distributed conversion and churn thresholds.</div>
  </div>
  <div class="vg-eq-card">
    <div class="vg-eq-title">2 · Word-of-Mouth Awareness Diffusion</div>
    <div class="vg-eq-formula">P(aware_t) = clip(r_mktg + ν · α_{t-1} · s_social, 0, 0.80)</div>
    <div class="vg-eq-desc">Unaware agents transition to Aware via paid/organic reach <code>r_mktg</code> compounded by endogenous viral loops scaled by virality <code>ν</code> and active adoption <code>α_{t-1}</code>.</div>
  </div>
  <div class="vg-eq-card">
    <div class="vg-eq-title">3 · Utility-Driven Conversion Score</div>
    <div class="vg-eq-formula">S = 0.30·need + 0.20·fit + 0.15·trust + 0.10·peer + 0.15·afford − 0.20·loyal − 0.15·switch</div>
    <div class="vg-eq-desc">Aware agents convert with monthly probability <code>σ(4·S − 3)</code> when exceeding their personal threshold, modeling friction against incumbent competitors.</div>
  </div>
  <div class="vg-eq-card">
    <div class="vg-eq-title">4 · Monte Carlo Epistemic Envelopes</div>
    <div class="vg-eq-formula">θ^(k) ~ U(0.60·θ₀, 1.40·θ₀) &nbsp;→&nbsp; {P10, P50, P90}_t</div>
    <div class="vg-eq-desc">Running K stochastic trials over perturbed priors isolates structural sensitivity and quantifies downside (P10) vs. upside (P90) revenue trajectories.</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )


def _store_and_finish(backend_url: str, result_json: dict, payload_dict: dict) -> None:
    st.session_state.update({
        "result":         result_json,
        "prefill":        payload_dict["product"],
        "prefill_config": payload_dict["config"],
        "payload":        payload_dict,
    })
    try:
        gd = requests.get(
            f"{backend_url}/api/graph/nodes",
            params={"product": result_json.get("product_name", "Product"), "limit": 50},
            timeout=8,
        )
        st.session_state["graph_data"] = gd.json() if gd.ok else {"source": "unavailable"}
    except Exception:
        st.session_state["graph_data"] = {"source": "unavailable"}
    st.rerun()


def _run_demo(backend_url: str) -> None:
    backend_url = backend_url.rstrip("/")
    with st.spinner("Simulating market dynamics (first request on free tier may take ~30s to wake server)…"):
        try:
            r  = requests.get(f"{backend_url}/api/demo",       timeout=120)
            ri = requests.get(f"{backend_url}/api/demo-input", timeout=30)
            r.raise_for_status()
            _store_and_finish(backend_url, r.json(), ri.json())
        except requests.exceptions.ConnectionError:
            st.error("Backend not running — open a terminal and run: `./run.sh backend`")
        except Exception as e:
            st.error(str(e))


def _run_preset(backend_url: str, preset: dict) -> None:
    backend_url = backend_url.rstrip("/")
    payload = {"product": preset["product"], "config": preset["config"]}
    with st.spinner(f"Running {preset['product']['product_name']} Monte Carlo benchmark…"):
        try:
            r = requests.post(f"{backend_url}/api/simulate/full", json=payload, timeout=120)
            r.raise_for_status()
            _store_and_finish(backend_url, r.json(), payload)
        except requests.exceptions.ConnectionError:
            st.error("Backend not running — open a terminal and run: `./run.sh backend`")
        except Exception as e:
            st.error(str(e))
