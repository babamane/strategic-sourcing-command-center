"""Interactive chatbot that uses Ollama (JSON tool-planning turns, plain-text answers)."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _default_ollama_base_url() -> str:
    """Match Ollama CLI env: OLLAMA_BASE_URL overrides; else OLLAMA_HOST (host:port or URL)."""

    explicit = os.getenv("OLLAMA_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = os.getenv("OLLAMA_HOST", "").strip()
    if host:
        return host.rstrip("/") if "://" in host else f"http://{host}".rstrip("/")
    return "http://127.0.0.1:11434"


def _candidate_base_urls(primary: str) -> list[str]:
    primary = primary.rstrip("/")
    urls = [primary]
    if "localhost" in primary:
        urls.append(primary.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in primary:
        urls.append(primary.replace("127.0.0.1", "localhost"))
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


@dataclass
class OllamaClientConfig:
    llm_provider: str = "ollama"
    ollama_base_url: str = field(default_factory=_default_ollama_base_url)
    ollama_model: str = "qwen2.5:14b"
    ollama_temperature: float = 0.1
    ollama_num_ctx: int = 16384
    ollama_num_predict: int = 1024
    ollama_num_thread: int = 14
    ollama_repeat_penalty: float = 1.15
    ollama_top_k: int = 40
    ollama_top_p: float = 0.9
    # auto: try /api/chat, then /api/generate on 404, then /v1/chat/completions on 404.
    # chat | generate | openai: force one endpoint. Override with env OLLAMA_API_MODE.
    ollama_api_mode: str = field(default_factory=lambda: os.getenv("OLLAMA_API_MODE", "auto").strip().lower())


def _ollama_options(cfg: OllamaClientConfig) -> dict[str, Any]:
    return {
        "temperature": cfg.ollama_temperature,
        "num_ctx": cfg.ollama_num_ctx,
        "num_predict": cfg.ollama_num_predict,
        "num_thread": cfg.ollama_num_thread,
        "repeat_penalty": cfg.ollama_repeat_penalty,
        "top_k": cfg.ollama_top_k,
        "top_p": cfg.ollama_top_p,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}\s*$", text)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Model did not return valid JSON: {text[:500]!r}")


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    """Flatten chat messages for /api/generate (single prompt)."""

    blocks: list[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        label = role.upper()
        blocks.append(f"[{label}]\n{content}")
    return "\n\n".join(blocks) + "\n\n[ASSISTANT]\n"


# Resolved transport for cfg.ollama_api_mode == "auto": "chat" | "generate" | "openai"
_ollama_resolved_endpoint: str | None = None


async def _post_openai_v1_chat(
    client: httpx.AsyncClient,
    cfg: OllamaClientConfig,
    messages: list[dict[str, str]],
    *,
    json_format: bool,
) -> str:
    """Ollama's OpenAI-compatible endpoint (same port, different path)."""

    url = f"{cfg.ollama_base_url.rstrip('/')}/v1/chat/completions"
    body: dict[str, Any] = {
        "model": cfg.ollama_model,
        "messages": messages,
        "stream": False,
        "temperature": cfg.ollama_temperature,
        "top_p": cfg.ollama_top_p,
    }
    if json_format:
        body["response_format"] = {"type": "json_object"}
    response = await client.post(url, json=body, timeout=600.0)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Unexpected Ollama /v1/chat/completions response: {data!r}")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected Ollama /v1/chat/completions message: {data!r}")
    return content


async def ensure_ollama_http(client: httpx.AsyncClient, cfg: OllamaClientConfig) -> None:
    """Pick a working base URL and optionally prefer OpenAI transport if native /api is missing."""

    global _ollama_resolved_endpoint

    lines: list[str] = []
    for base in _candidate_base_urls(cfg.ollama_base_url):
        tags_url = f"{base}/api/tags"
        models_url = f"{base}/v1/models"
        try:
            rt = await client.get(tags_url, timeout=10)
            lines.append(f"GET {tags_url} -> HTTP {rt.status_code}")
            if rt.status_code == 200:
                cfg.ollama_base_url = base.rstrip("/")
                print(f"Using Ollama at {cfg.ollama_base_url} (native /api/tags OK).")
                return
        except httpx.RequestError as exc:
            lines.append(f"GET {tags_url} -> {exc!r}")
        try:
            rv = await client.get(models_url, timeout=10)
            lines.append(f"GET {models_url} -> HTTP {rv.status_code}")
            if rv.status_code == 200:
                cfg.ollama_base_url = base.rstrip("/")
                _ollama_resolved_endpoint = "openai"
                print(
                    f"Using Ollama at {cfg.ollama_base_url} (/v1/models OK). "
                    "Native /api/chat was not verified — completions will use /v1/chat/completions."
                )
                return
        except httpx.RequestError as exc:
            lines.append(f"GET {models_url} -> {exc!r}")

    raise RuntimeError(
        "Could not find a running Ollama server.\n"
        + "\n".join(f"  {line}" for line in lines)
        + "\n\nFix: run `ollama serve` in a terminal, or set OLLAMA_BASE_URL (e.g. http://127.0.0.1:11434). "
        "If you use Docker/WSL, point the URL at the machine where `ollama serve` listens."
    )


async def _post_ollama_chat_api(
    client: httpx.AsyncClient,
    cfg: OllamaClientConfig,
    messages: list[dict[str, str]],
    *,
    json_format: bool,
) -> str:
    url = f"{cfg.ollama_base_url.rstrip('/')}/api/chat"
    body: dict[str, Any] = {
        "model": cfg.ollama_model,
        "messages": messages,
        "stream": False,
        "options": _ollama_options(cfg),
    }
    if json_format:
        body["format"] = "json"
    response = await client.post(url, json=body, timeout=600.0)
    response.raise_for_status()
    data = response.json()
    msg = data.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected Ollama /api/chat response: {data!r}")
    return content


async def _post_ollama_generate_api(
    client: httpx.AsyncClient,
    cfg: OllamaClientConfig,
    messages: list[dict[str, str]],
    *,
    json_format: bool,
) -> str:
    url = f"{cfg.ollama_base_url.rstrip('/')}/api/generate"
    body: dict[str, Any] = {
        "model": cfg.ollama_model,
        "prompt": _messages_to_prompt(messages),
        "stream": False,
        "options": _ollama_options(cfg),
    }
    if json_format:
        body["format"] = "json"
    response = await client.post(url, json=body, timeout=600.0)
    response.raise_for_status()
    data = response.json()
    content = data.get("response")
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected Ollama /api/generate response: {data!r}")
    return content


async def _ollama_completion(
    client: httpx.AsyncClient,
    cfg: OllamaClientConfig,
    messages: list[dict[str, str]],
    *,
    json_format: bool,
) -> str:
    """Call Ollama: native /api/chat, /api/generate, or OpenAI-compatible /v1/chat/completions."""

    global _ollama_resolved_endpoint

    mode = (cfg.ollama_api_mode or "auto").lower()
    if mode == "openai":
        return await _post_openai_v1_chat(client, cfg, messages, json_format=json_format)
    if mode == "generate":
        return await _post_ollama_generate_api(client, cfg, messages, json_format=json_format)
    if mode == "chat":
        return await _post_ollama_chat_api(client, cfg, messages, json_format=json_format)

    if _ollama_resolved_endpoint == "openai":
        return await _post_openai_v1_chat(client, cfg, messages, json_format=json_format)
    if _ollama_resolved_endpoint == "generate":
        return await _post_ollama_generate_api(client, cfg, messages, json_format=json_format)
    if _ollama_resolved_endpoint == "chat":
        return await _post_ollama_chat_api(client, cfg, messages, json_format=json_format)

    try:
        text = await _post_ollama_chat_api(client, cfg, messages, json_format=json_format)
        _ollama_resolved_endpoint = "chat"
        return text
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        try:
            text = await _post_ollama_generate_api(client, cfg, messages, json_format=json_format)
            _ollama_resolved_endpoint = "generate"
            print("\n(note) /api/chat returned 404 — using /api/generate for this session.\n")
            return text
        except httpx.HTTPStatusError as exc2:
            if exc2.response.status_code != 404:
                raise
            text = await _post_openai_v1_chat(client, cfg, messages, json_format=json_format)
            _ollama_resolved_endpoint = "openai"
            print(
                "\n(note) Native /api/chat and /api/generate returned 404 — "
                "using OpenAI-compatible /v1/chat/completions for this session.\n"
            )
            return text


async def _tool_catalog_block(mcp) -> str:
    tools = await mcp.list_tools()
    lines = []
    for t in tools:
        first = (t.description or "").splitlines()[0] if t.description else ""
        lines.append(f"- {t.name}: {first}")
    return "\n".join(lines)


async def _call_mcp_tool(mcp, name: str, arguments: dict[str, Any]) -> Any:
    result = await mcp.call_tool(name, arguments or {})
    return result.structured_content


async def _run_turn(mcp, client: httpx.AsyncClient, cfg: OllamaClientConfig, history: list[dict[str, str]]) -> str:
    planner_system = (
        "You are the planning component for a SaaS spend assistant. "
        "Reply with a single JSON object only (no markdown).\n"
        'Either {"phase":"tools","calls":[{"name":"<tool>","arguments":{...}}, ...]} '
        'to request read-only or write tools, '
        'or {"phase":"answer","text":"<plain text for the user>"} when you can answer directly '
        "without more tools.\n"
        "Rules: prefer tools when the user asks about live license, renewal, ghost, utilization, "
        "reclamation, true-up, or forecast data. "
        "Write tools (trigger_*) must first be called with confirmed=false for preview unless the user "
        "clearly already confirmed; only use confirmed=true after explicit user approval in the conversation.\n"
        "Available tools:\n"
        "Rules: ... "
        "Pass vendor names exactly as the user typed them — do not normalize, correct, or infer vendor names. "
        "accepted vendor names Atlassify, Nexaflow, Cloudora if identified do not change the names"
        f"{await _tool_catalog_block(mcp)}"
    )   
    plan_messages = [{"role": "system", "content": planner_system}, *history]
    raw = await _ollama_completion(client, cfg, plan_messages, json_format=True)
    plan = _extract_json_object(raw)
    phase = plan.get("phase")
    if phase == "answer":
        text = plan.get("text")
        if not isinstance(text, str):
            raise ValueError("answer phase requires string 'text'")
        return text
    if phase != "tools":
        raise ValueError(f"Unknown phase {phase!r} in {plan!r}")
    calls = plan.get("calls") or []
    if not isinstance(calls, list):
        raise ValueError("'calls' must be a list")
    tool_blocks: list[str] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        args = call.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(args, dict):
            continue
        payload = await _call_mcp_tool(mcp, name, args)
        tool_blocks.append(json.dumps({"tool": name, "arguments": args, "result": payload}, default=str))
    tool_report = "\n\n".join(tool_blocks) if tool_blocks else "(no tools executed)"
    final_messages = [
        {
            "role": "system",
            "content": (
                "You are the SaaS spend assistant. Using the prior conversation and the tool results JSON, "
                "write a concise, accurate plain-text answer for the user. Do not output JSON."
            ),
        },
        *history,
        {"role": "user", "content": f"Tool results:\n{tool_report}\n\nAnswer the user in plain language."},
    ]
    return await _ollama_completion(client, cfg, final_messages, json_format=False)


async def chat_loop(cfg: OllamaClientConfig | None = None) -> None:
    from mcp_server.server import mcp

    cfg = cfg or OllamaClientConfig()
    print("SaaS Spend chatbot (Ollama). Type 'quit' to exit.")
    history: list[dict[str, str]] = []
    async with httpx.AsyncClient() as client:
        await ensure_ollama_http(client, cfg)
        while True:
            line = input("\nYou> ").strip()
            if line.lower() in {"quit", "exit"}:
                break
            if not line:
                continue
            history.append({"role": "user", "content": line})
            try:
                reply = await _run_turn(mcp, client, cfg, history)
            except Exception as exc:  # noqa: BLE001
                print(f"\nAssistant> (error) {exc}")
                history.pop()
                continue
            print(f"\nAssistant> {reply}")
            history.append({"role": "assistant", "content": reply})


def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
