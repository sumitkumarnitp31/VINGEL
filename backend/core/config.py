import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini AI ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
USE_GEMINI     = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")

# ── Neo4j ─────────────────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "vingel_password")
USE_NEO4J      = os.getenv("USE_NEO4J", "true").lower() not in ("false", "0", "no")

# ── Simulation defaults ───────────────────────────────────────────────────────
N_USERS_DEFAULT       = 100_000
N_MONTHS_DEFAULT      = 24
N_MONTE_CARLO_DEFAULT = 100
