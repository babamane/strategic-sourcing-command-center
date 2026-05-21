import asyncio

from mcp_server.server import mcp


READ_TOOLS = {
    "get_trueup_exposure",
    "get_trueup_breakdown",
    "get_ghost_summary",
    "get_ghost_detail",
    "get_reclamation_candidates",
    "get_utilization_summary",
    "get_renewal_pressure",
    "get_license_demand_forecast",
    "get_active_demand",
}
WRITE_TOOLS = {
    "trigger_reclamation_review",
    "trigger_renewal_alert",
    "trigger_ghost_ticket",
    "send_churn_notification",
}


def test_mcp_tool_inventory_and_schemas():
    async def _run():
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert names == READ_TOOLS | WRITE_TOOLS

        for t in tools:
            assert t.description and t.description.strip()

        by_name = {t.name: t for t in tools}
        for name in READ_TOOLS:
            params = by_name[name].parameters or {}
            props = params.get("properties") or {}
            assert "vendor" in props, f"{name} missing vendor parameter"

        for name in WRITE_TOOLS:
            props = (by_name[name].parameters or {}).get("properties") or {}
            assert "confirmed" in props, f"{name} missing confirmed flag"

    asyncio.run(_run())


def test_read_tool_smoke():
    async def _run():
        result = await mcp.call_tool("get_trueup_exposure", {})
        assert result.structured_content is not None

    asyncio.run(_run())


def test_write_tool_preview_pattern():
    from processing.context_builder import build_context

    async def _run():
        ctx = build_context()
        vendor = ctx.active_vendors[0]
        preview = await mcp.call_tool("trigger_ghost_ticket", {"vendor": vendor, "confirmed": False})
        body = preview.structured_content
        assert isinstance(body, dict)
        assert body.get("preview") is True

    asyncio.run(_run())
