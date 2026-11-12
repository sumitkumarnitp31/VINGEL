"""Graph tab — Neo4j population visualisation with pyvis."""
import math
import json as _json
import streamlit as st
import streamlit.components.v1 as st_components
import pandas as pd
import requests

_SEG_COLORS    = ["#818cf8", "#34d399", "#fbbf24", "#f472b6", "#a855f7", "#0ea5e9", "#f97316", "#14b8a6"]
_STATUS_COLORS = {0: "#1e2545", 1: "#38bdf8", 2: "#4ade80", 3: "#f87171"}
_STATUS_SIZES  = {0: 5,        1: 7,        2: 12,        3: 6}
_STATUS_LABELS = {0: "Unaware", 1: "Aware",  2: "Active ✓", 3: "Churned ✗"}


def _build_graph_html(gd: dict, is_dark: bool = True) -> str:
    from pyvis.network import Network

    bg = "#050712" if is_dark else "#f0f0f5"
    fc = "#e2e8f0" if is_dark else "#18181b"

    net = Network(
        height="640px", width="100%", bgcolor=bg,
        font_color=fc, cdn_resources="in_line", directed=False,
    )
    net.set_options(_json.dumps({
        "physics": {
            "enabled": True,
            "forceAtlas2Based": {
                "gravitationalConstant": -80, "centralGravity": .005,
                "springLength": 90, "springConstant": .08, "damping": .45, "avoidOverlap": .6,
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 180, "updateInterval": 25, "fit": True},
        },
        "edges":  {"smooth": {"enabled": True, "type": "continuous"}, "color": {"inherit": False}},
        "nodes":  {"borderWidth": 1.5, "shadow": {"enabled": True, "size": 6}},
        "interaction": {"hover": True, "tooltipDelay": 80, "hideEdgesOnDrag": True},
    }))

    product_name = gd.get("product_name", "Product")
    segments     = gd.get("segments", [])
    users        = gd.get("users", [])

    net.add_node(
        "PRODUCT",
        label=product_name[:22] + ("…" if len(product_name) > 22 else ""),
        color={"background": "#f59e0b", "border": "#fcd34d",
               "highlight": {"background": "#fde68a", "border": "#f59e0b"}},
        size=42, shape="dot",
        font={"color": "#0f172a", "size": 13, "bold": True},
        title=(f"<b style='color:#f59e0b;font-size:14px'>{product_name}</b><br>"
               f"<span style='color:#64748b'>{gd.get('total_stored',0):,} nodes in Neo4j</span>"),
        x=0, y=0, physics=False,
    )

    n_segs = max(len(segments), 1)
    seg_id_map: dict[str, tuple[str, int]] = {}

    for i, seg in enumerate(segments):
        sid    = f"SEG_{i}"
        sname  = seg.get("seg_name", f"Segment {i}")
        color  = _SEG_COLORS[i % len(_SEG_COLORS)]
        seg_id_map[sname] = (sid, i)
        angle  = math.radians(90 + i * (360 / n_segs))
        sx, sy = int(400 * math.cos(angle)), int(400 * math.sin(angle))
        net.add_node(
            sid, label=sname[:18],
            color={"background": color, "border": color,
                   "highlight": {"background": color, "border": "#fff"}},
            size=28, shape="dot", font={"color": "#f1f5f9", "size": 11},
            title=(f"<b style='color:{color}'>{sname}</b><br>"
                   f"Share: <b>{seg.get('share',0):.0%}</b><br>"
                   f"<span style='color:#64748b;font-size:11px'>{seg.get('desc','')}</span>"),
            x=sx, y=sy, physics=False,
        )
        net.add_edge("PRODUCT", sid,
                     color={"color": color, "opacity": .7}, width=2.5, title="PART_OF")

    import random as _rnd
    _rnd.seed(42)
    for user in users:
        sname = user.get("seg", "")
        info  = seg_id_map.get(sname)
        if not info:
            continue
        sid, si = info
        seg_angle = math.radians(90 + si * (360 / n_segs))
        sx = 400 * math.cos(seg_angle)
        sy = 400 * math.sin(seg_angle)
        ua, ur = math.radians(_rnd.uniform(0, 360)), _rnd.uniform(65, 210)
        ux, uy = int(sx + ur * math.cos(ua)), int(sy + ur * math.sin(ua))
        status     = user.get("status", 0)
        node_color = _STATUS_COLORS.get(status, "#1e2545")
        seg_color  = _SEG_COLORS[si % len(_SEG_COLORS)]
        net.add_node(
            user.get("uid", f"u_{_rnd.random()}"), label="",
            color={"background": node_color, "border": seg_color,
                   "highlight": {"background": node_color, "border": "#fff"}},
            size=_STATUS_SIZES.get(status, 5), shape="dot", font={"size": 0},
            title=(f"<b style='color:{node_color}'>{_STATUS_LABELS.get(status,'')}</b>"
                   f" · <span style='color:#64748b'>{sname}</span><br>"
                   f"Need: <b>{user.get('need_level',0):.2f}</b> "
                   f"Trust: <b>{user.get('trust_score',0):.2f}</b><br>"
                   f"Income: <b>${user.get('income_monthly',0):,.0f}/mo</b>"),
            x=ux, y=uy,
        )
        net.add_edge(user.get("uid"), sid,
                     color={"color": "#111428", "opacity": .5}, width=.4, title="IN_SEGMENT")

    return net.generate_html(notebook=False)


def _synthesize_graph_from_result(result: dict, sample_per_seg: int = 28) -> dict | None:
    """Build a representative PyVis graph payload from simulation results when Neo4j is offline."""
    if not result or not result.get("segments"):
        return None
    import random as _rnd
    rng = _rnd.Random(42)

    segs_raw = result.get("segments", [])
    adopt_map = {a["segment_name"]: a.get("adoption_rate", 0.0) for a in result.get("segment_adoption", [])}
    last_m = (result.get("base_monthly") or [{}])[-1]
    churn_rate = last_m.get("churn_rate", 0.04)

    segments = [
        {
            "seg_name": s["segment_name"],
            "share": s.get("share", 0.0),
            "desc": s.get("description", ""),
            "ps": s.get("price_sensitivity", 0.5),
            "ta": s.get("tech_affinity", 0.5),
        }
        for s in segs_raw
    ]

    users = []
    counts = {"unaware": 0, "aware": 0, "active": 0, "churned": 0}
    status_keys = {0: "unaware", 1: "aware", 2: "active", 3: "churned"}

    for si, s in enumerate(segs_raw):
        sname = s["segment_name"]
        p_active = min(0.85, max(0.02, float(adopt_map.get(sname, 0.05))))
        p_churned = min(0.25, p_active * min(0.8, churn_rate * 4.0))
        p_aware = min(0.50, max(0.10, (1.0 - p_active - p_churned) * 0.45))
        n_nodes = max(12, int(round(sample_per_seg * (0.6 + s.get("share", 0.15) * 2.5))))

        for ui in range(n_nodes):
            r = rng.random()
            if r < p_active:
                st_code = 2
            elif r < p_active + p_churned:
                st_code = 3
            elif r < p_active + p_churned + p_aware:
                st_code = 1
            else:
                st_code = 0
            counts[status_keys[st_code]] += 1
            lo_inc = float(s.get("income_monthly_min", 2500))
            hi_inc = float(s.get("income_monthly_max", 8000))
            users.append({
                "uid": f"sim_{si}_{ui}",
                "seg": sname,
                "status": st_code,
                "need_level": round(min(1.0, max(0.0, s.get("need_urgency", 0.5) + rng.uniform(-0.15, 0.15))), 2),
                "trust_score": round(min(1.0, max(0.0, 1.0 - s.get("trust_threshold", 0.5) + rng.uniform(-0.15, 0.15))), 2),
                "income_monthly": round(rng.uniform(lo_inc, hi_inc), 0),
            })

    return {
        "source": "simulated_local",
        "product_name": result.get("product_name", "Product"),
        "total_stored": len(users),
        "segments": segments,
        "users": users,
        "stats": counts,
    }


def render_graph_preview(gd: dict, is_dark: bool = True, result: dict | None = None) -> None:
    """Embed-friendly graph view — no controls, used on the Overview page."""
    source = gd.get("source", "unavailable")
    if source in ("unavailable", "not_found") or str(source).startswith("error"):
        synth = _synthesize_graph_from_result(result) if result else None
        if synth is None:
            st.caption("Run a simulation first to view the population topology.")
            return
        gd = synth
        st.caption("Simulated sample topology (connect Neo4j Desktop for full 2,000-node DB persistence).")
    try:
        st_components.html(_build_graph_html(gd, is_dark), height=560, scrolling=False)
    except ImportError:
        st.warning("pyvis not installed — run `./run.sh install`")
    except Exception as e:
        st.warning(f"Graph render error: {e}")


def render_graph(backend_url: str, result: dict, is_dark: bool = True) -> None:
    gd     = st.session_state.get("graph_data", {})
    source = gd.get("source", "unavailable")

    card_bg  = "rgba(15,15,24,.92)"       if is_dark else "rgba(255,255,255,.97)"
    card_bdr = "rgba(255,255,255,.08)"   if is_dark else "rgba(0,0,0,.08)"
    lbl_c    = "#8888a0"                  if is_dark else "#7070a0"
    val_c    = "#f4f4f8"                  if is_dark else "#09090d"

    # ── Controls ──────────────────────────────────────────────────────────
    rc1, rc2, _ = st.columns([1, 1, 4])
    with rc1:
        if st.button("🔄  Refresh", use_container_width=True):
            try:
                r = requests.get(f"{backend_url}/api/graph/nodes",
                                 params={"product": result.get("product_name",""), "limit": 50},
                                 timeout=30)
                st.session_state["graph_data"] = r.json() if r.ok else {"source": "unavailable"}
                gd     = st.session_state["graph_data"]
                source = gd.get("source", "unavailable")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    with rc2:
        try:
            sr = requests.get(f"{backend_url}/api/graph/status", timeout=5)
            s  = sr.json() if sr.ok else {}
            if s.get("connected"):
                st.success("Neo4j ✓")
            else:
                st.warning("Neo4j offline")
        except Exception:
            st.warning("Neo4j offline")

    # ── Unavailable state: synthesize representative sample from result ───────
    is_synth = False
    if source in ("unavailable", "not_found") or source.startswith("error"):
        synth = _synthesize_graph_from_result(result, sample_per_seg=35)
        if synth is None:
            st.divider()
            st.info("Run a simulation first, then click Refresh.")
            return
        gd = synth
        is_synth = True
        st.info("Showing interactive simulated population sample (connect Neo4j for persistent graph DB storage).")

    # ── Stats KPIs ────────────────────────────────────────────────────────
    stats        = gd.get("stats", {})
    total_stored = gd.get("total_stored", 0)
    STATUS_C     = {"unaware": "#263050", "aware": "#38bdf8", "active": "#4ade80", "churned": "#f87171"}

    ks = st.columns(5)
    ks[0].markdown(
        f'<div style="background:{card_bg};border:1px solid {card_bdr};'
        f'border-radius:14px;padding:14px;text-align:center">'
        f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:{lbl_c};margin-bottom:6px">{"Sampled Nodes" if is_synth else "Stored Nodes"}</div>'
        f'<div style="font-size:1.6rem;font-weight:900;color:{val_c}">{total_stored:,}</div>'
        f'<div style="font-size:9.5px;color:{lbl_c}">{"in-memory topology" if is_synth else "users in Neo4j"}</div></div>',
        unsafe_allow_html=True,
    )
    for i, (lbl, key) in enumerate([("Unaware","unaware"),("Aware","aware"),
                                      ("Active","active"),("Churned","churned")], 1):
        cnt = stats.get(key, 0)
        c   = STATUS_C[key]
        ks[i].markdown(
            f'<div style="background:{card_bg};border:1px solid {c}22;'
            f'border-radius:14px;padding:14px;text-align:center">'
            f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:{c};margin-bottom:6px">{lbl}</div>'
            f'<div style="font-size:1.6rem;font-weight:900;color:{c}">{cnt:,}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Legend ────────────────────────────────────────────────────────────
    legend_color = "#55556a" if is_dark else "#707088"
    st.markdown(f"""
    <div class="vg-legend">
      <span><span class="vg-dot" style="background:#f59e0b;box-shadow:0 0 8px #f59e0b"></span>Product</span>
      <span><span class="vg-dot" style="background:#818cf8;box-shadow:0 0 8px #818cf8"></span>Segment</span>
      <span><span class="vg-dot" style="background:#263050"></span>Unaware</span>
      <span><span class="vg-dot" style="background:#38bdf8;box-shadow:0 0 6px #38bdf8"></span>Aware</span>
      <span><span class="vg-dot" style="background:#4ade80;box-shadow:0 0 6px #4ade80"></span>Active</span>
      <span><span class="vg-dot" style="background:#f87171;box-shadow:0 0 6px #f87171"></span>Churned</span>
      <span style="color:{legend_color};font-size:.75rem">· Hover nodes for details · Active = largest</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Graph ─────────────────────────────────────────────────────────────
    try:
        st_components.html(_build_graph_html(gd, is_dark), height=660, scrolling=False)
    except ImportError:
        st.error("pyvis not installed — run `./run.sh install`")
    except Exception as e:
        st.error(f"Graph render error: {e}")

    # ── Segment table ─────────────────────────────────────────────────────
    with st.expander("Segment breakdown"):
        rows = [
            {"Segment":    s.get("seg_name"),
             "Share":      f"{s.get('share',0):.0%}",
             "Price Sens": f"{s.get('ps',0):.2f}",
             "Tech Aff":   f"{s.get('ta',0):.2f}",
             "Description": s.get("desc","")}
            for s in gd.get("segments", [])
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
