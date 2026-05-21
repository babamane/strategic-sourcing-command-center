from processing.context_builder import ProcessingContext, build_context


def test_build_context_populates_all_collections():
    ctx = build_context()

    assert isinstance(ctx, ProcessingContext)
    assert ctx.licenses
    assert ctx.entitlement
    assert ctx.active_contracts
    assert ctx.contract_history
    assert ctx.active_employees
    assert ctx.exited_employees
    assert ctx.future_hires
    assert ctx.audit_date
    assert ctx.active_vendors
    assert ctx.fetched_at


def test_build_context_contract_history_includes_superseded():
    ctx = build_context()

    assert ctx.contract_history
    assert any(row["contract_status"] == "superseded" for row in ctx.contract_history)


def test_build_context_vendor_filter():
    ctx = build_context(vendor="Nexaflow")

    assert ctx.active_vendors == ["Nexaflow"]
    assert {row["vendor"] for row in ctx.licenses} == {"Nexaflow"}
    assert {row["vendor"] for row in ctx.entitlement} == {"Nexaflow"}


def test_build_context_returns_cached_result_within_ttl():
    from processing import context_builder as cb

    cb._context_cache.clear()
    ctx1 = build_context(vendor=None, version=None)
    ctx2 = build_context(vendor=None, version=None)
    assert ctx1 is ctx2
    assert ctx1.fetched_at == ctx2.fetched_at
