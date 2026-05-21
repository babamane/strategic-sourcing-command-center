"""FastMCP server entrypoint (stdio or streamable-http)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastmcp import FastMCP

mcp = FastMCP(
    "saas-spend-mcp",
    instructions=(
        "SaaS spend management assistant. Inspect computed_at on tool results to judge data freshness. "
        "Pass vendor= to focus on one vendor; omit vendor for portfolio-wide results. "
        "Write tools require a preview call first, then confirmed=true after human approval."
    ),
)

import mcp_server.tools  # noqa: E402, F401 — registers @mcp.tool handlers


if __name__ == "__main__":
    transport = os.getenv("FASTMCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
    else:
        mcp.run()
