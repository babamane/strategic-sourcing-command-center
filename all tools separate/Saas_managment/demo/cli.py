"""Thin interactive shell calling FastMCP tools in-process (no HTTP, no Claude Desktop)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _coerce(value: str) -> bool | float | int | str:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


async def _call_tool(mcp, tool_name: str, kwargs: dict) -> object:
    result = await mcp.call_tool(tool_name, kwargs)
    return result.structured_content


def run() -> None:
    from mcp_server.server import mcp

    print("SaaS Spend CLI — type 'tools' to list, 'quit' to exit")

    while True:
        line = input("\n> ").strip()
        if line == "quit":
            break
        if not line:
            continue
        if line == "tools":

            async def list_names():
                tools = await mcp.list_tools()
                for t in tools:
                    desc = (t.description or "").splitlines()[0] if t.description else ""
                    print(f"  {t.name:40s} {desc}")

            asyncio.run(list_names())
            continue
        parts = line.split()
        tool_name = parts[0]
        raw_kwargs = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
        kwargs = {k: _coerce(v) for k, v in raw_kwargs.items()}
        result = asyncio.run(_call_tool(mcp, tool_name, kwargs))
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    run()
