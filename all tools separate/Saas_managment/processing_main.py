"""Manual runner for Phase 1C processors."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime

from processing.breakdown_enricher import get_trueup_breakdown
from processing.context_builder import build_context
from processing.ghost_detector import get_ghost_summary
from processing.active_demand_processor import get_active_demand_history, get_active_demand_series
from processing.license_demand_forecaster import get_license_demand_forecast
from processing.reclamation_detector import get_reclamation_candidates
from processing.renewal_pressure_forecaster import get_renewal_pressure
from processing.trueup_processor import get_trueup_exposure
from processing.utilization_aggregator import get_utilization_summary


def _json_default(value: object) -> object:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _summarize(rows: list[object]) -> dict:
    return {"count": len(rows), "sample": rows[0] if rows else None}


def _print_section(title: str, rows: list[object], as_json: bool, full: bool) -> None:
    payload: object = rows if full else _summarize(rows)
    print(f"\n== {title} ==")
    if as_json:
        print(json.dumps(payload, indent=2, default=_json_default))
    else:
        print(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual runner for Phase 1C processing.")
    parser.add_argument("--vendor", default=None, help="Optional active vendor filter.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--full", action="store_true", help="Print full result rows.")
    args = parser.parse_args()

    ctx = build_context(vendor=args.vendor)
    _print_section("get_trueup_exposure", get_trueup_exposure(ctx, vendor=args.vendor), args.json, args.full)
    _print_section("get_trueup_breakdown", get_trueup_breakdown(ctx, vendor=args.vendor), args.json, args.full)
    _print_section("get_ghost_summary", get_ghost_summary(ctx, vendor=args.vendor), args.json, args.full)
    _print_section(
        "get_reclamation_candidates",
        get_reclamation_candidates(ctx, vendor=args.vendor),
        args.json,
        args.full,
    )
    _print_section("get_utilization_summary", get_utilization_summary(ctx, vendor=args.vendor), args.json, args.full)
    _print_section(
        "get_active_demand_history",
        get_active_demand_history(ctx, vendor=args.vendor),
        args.json,
        args.full,
    )
    _print_section(
        "get_active_demand_series",
        get_active_demand_series(ctx, vendor=args.vendor),
        args.json,
        args.full,
    )
    _print_section(
        "get_license_demand_forecast",
        get_license_demand_forecast(ctx, vendor=args.vendor),
        args.json,
        args.full,
    )
    _print_section("get_renewal_pressure", get_renewal_pressure(ctx, vendor=args.vendor), args.json, args.full)


if __name__ == "__main__":
    main()
