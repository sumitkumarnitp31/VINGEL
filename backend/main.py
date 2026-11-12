"""
VINGEL Market Simulator — REST API  v0.5.0

Simulation
──────────
GET  /health
GET  /api/demo-input
GET  /api/demo
POST /api/assumptions
POST /api/segments
POST /api/simulate/monthly
POST /api/simulate/monte-carlo
POST /api/simulate/full

Graph (Neo4j)
─────────────
GET  /api/graph/status
GET  /api/graph/nodes?product=…&limit=50
"""
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import USE_GEMINI, GEMINI_MODEL, USE_NEO4J, NEO4J_URI
from backend.core.models import (
    ProductInput, SimulateRequest, SimulationConfig,
    BusinessAssumptions, CustomerSegment, MonthlyMetrics,
    MonteCarloResult, SimulationResult,
)
from backend.engines.idea_parser import parse_idea
from backend.engines.segmentation import generate_segments
from backend.engines.simulation import generate_population, build_product_params, run_simulation
from backend.engines.monte_carlo import run_monte_carlo
from backend.core.graph import push_population, get_graph_data, is_connected

app = FastAPI(
    title="VINGEL Market Simulator",
    version="0.5.0",
    description="Gemini AI assumptions · vectorised NumPy funnel · Monte Carlo · Neo4j graph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Demo fixture ──────────────────────────────────────────────────────────────

_DEMO_PRODUCT = ProductInput(
    product_name="ProjectFlow Pro",
    product_description="AI-powered project management that auto-schedules tasks, detects bottlenecks, and syncs with Slack/GitHub.",
    target_market="SMB software teams, 5–50 employees",
    price=49.0,
    billing_model="monthly_subscription",
    geography=["US", "Canada", "UK"],
    competitors=["Asana", "Monday.com", "Linear"],
    channels=["Content SEO", "Product-led growth", "Paid LinkedIn"],
    features=[
        "AI task scheduling",
        "Slack integration",
        "GitHub sync",
        "Bottleneck alerts",
        "Team analytics dashboard",
    ],
)

_DEMO_CONFIG = SimulationConfig(n_users=10_000, n_months=12, n_monte_carlo=20, random_seed=42)


# ── Shared build helper ───────────────────────────────────────────────────────

def _build_result(req: SimulateRequest) -> SimulationResult:
    assumptions, _ = parse_idea(req.product)
    segments, _    = generate_segments(req.product)
    pop     = generate_population(segments, req.config.n_users, seed=req.config.random_seed)
    params  = build_product_params(req.product, assumptions)

    # Monte Carlo (includes base run + base_status)
    mc = run_monte_carlo(pop, params, req.config, segments)

    # Push population + final statuses to Neo4j (fire-and-forget; errors swallowed)
    push_population(req.product.product_name, segments, pop, mc["base_status"])

    base = mc["base_monthly"]
    return SimulationResult(
        product_name=req.product.product_name,
        assumptions=assumptions,
        segments=segments,
        base_monthly=base,
        mc_p10=mc["mc_p10"],
        mc_p50=mc["mc_p50"],
        mc_p90=mc["mc_p90"],
        segment_adoption=mc["segment_adoption"],
        final_mrr=round(base[-1].mrr, 2),
        final_arr=round(base[-1].mrr * 12, 2),
        peak_adoption_rate=round(max(m.adoption_rate for m in base), 4),
        final_churn_rate=round(base[-1].churn_rate, 4),
    )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health():
    return {
        "status":   "ok",
        "version":  "0.5.0",
        "ai_mode":  f"gemini ({GEMINI_MODEL})" if USE_GEMINI else "heuristic",
        "neo4j":    "connected" if is_connected() else "unavailable",
        "python":   sys.version,
    }


# ── Demo ──────────────────────────────────────────────────────────────────────

@app.get("/api/demo-input", tags=["demo"])
def demo_input():
    return {"product": _DEMO_PRODUCT.model_dump(), "config": _DEMO_CONFIG.model_dump()}


@app.get("/api/demo", response_model=SimulationResult, tags=["demo"])
def demo():
    return _build_result(SimulateRequest(product=_DEMO_PRODUCT, config=_DEMO_CONFIG))


# ── Step-by-step ──────────────────────────────────────────────────────────────

@app.post("/api/assumptions", tags=["step"])
def get_assumptions(product: ProductInput):
    assumptions, used_gemini = parse_idea(product)
    return {**assumptions.model_dump(), "_source": "gemini" if used_gemini else "heuristic"}


@app.post("/api/segments", tags=["step"])
def get_segments(product: ProductInput):
    segments, used_gemini = generate_segments(product)
    return {
        "segments": [s.model_dump() for s in segments],
        "_source": "gemini" if used_gemini else "heuristic",
    }


@app.post("/api/simulate/monthly", response_model=list[MonthlyMetrics], tags=["simulate"])
def simulate_monthly(req: SimulateRequest):
    assumptions, _ = parse_idea(req.product)
    segments, _    = generate_segments(req.product)
    pop    = generate_population(segments, req.config.n_users, seed=req.config.random_seed)
    params = build_product_params(req.product, assumptions)
    metrics, _ = run_simulation(pop, params, seed=req.config.random_seed, n_months=req.config.n_months)
    return metrics


@app.post("/api/simulate/monte-carlo", response_model=MonteCarloResult, tags=["simulate"])
def simulate_monte_carlo(req: SimulateRequest):
    assumptions, _ = parse_idea(req.product)
    segments, _    = generate_segments(req.product)
    pop    = generate_population(segments, req.config.n_users, seed=req.config.random_seed)
    params = build_product_params(req.product, assumptions)
    mc = run_monte_carlo(pop, params, req.config, segments)
    return MonteCarloResult(
        base_monthly=mc["base_monthly"],
        mc_p10=mc["mc_p10"],
        mc_p50=mc["mc_p50"],
        mc_p90=mc["mc_p90"],
        segment_adoption=mc["segment_adoption"],
    )


@app.post("/api/simulate/full", response_model=SimulationResult, tags=["simulate"])
def simulate_full(req: SimulateRequest):
    return _build_result(req)


# ── Graph (Neo4j) ─────────────────────────────────────────────────────────────

@app.get("/api/graph/status", tags=["graph"])
def graph_status():
    """Check whether the Neo4j connection is live."""
    connected = is_connected()
    return {
        "connected": connected,
        "uri":       NEO4J_URI if connected else None,
        "message":   "Neo4j is reachable" if connected
                     else "Neo4j unavailable — start with: docker-compose up -d neo4j",
    }


@app.get("/api/graph/nodes", tags=["graph"])
def graph_nodes(
    product: str = Query(..., description="Product name used in the last simulation"),
    limit:   int = Query(50,  description="Max user nodes to return per segment (default 50)"),
):
    """
    Return product + segment + sampled user nodes for pyvis visualization.
    Queries Neo4j for nodes created during the last simulation run.
    """
    data = get_graph_data(product_name=product, display_per_segment=limit)
    return data

