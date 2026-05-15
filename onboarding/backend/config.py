import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

# ── Search (DuckDuckGo — free, no API key required) ──────────────────────────
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))

# ── Database ──────────────────────────────────────────────────────────────────
# Swap to postgresql+psycopg2://user:pass@host/db for production PostgreSQL
DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite:///./onboarding.db")

# LangGraph checkpoint store (SQLite file, separate from main DB)
CHECKPOINT_DB   = os.getenv("CHECKPOINT_DB", "./checkpoints.db")

# ── API ───────────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8090"))
