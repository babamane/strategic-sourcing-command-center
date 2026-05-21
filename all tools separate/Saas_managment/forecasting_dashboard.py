"""Streamlit dashboard for inspecting forecasting processor output."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Iterable

import pandas as pd
import streamlit as st

from processing.active_demand_processor import get_active_demand_history
from processing.context_builder import build_context
from processing.license_demand_forecaster import get_license_demand_forecast


st.set_page_config(page_title="SaaS Forecast Inspector", layout="wide")


def _as_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _add_months(month: str, offset: int) -> str:
    year, month_number = [int(part) for part in month.split("-", 1)]
    month_index = (year * 12 + month_number - 1) + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _month_range(start_month: str, end_month: str) -> list[str]:
    months: list[str] = []
    current = start_month
    while current <= end_month:
        months.append(current)
        current = _add_months(current, 1)
    return months


def _previous_month(value: date) -> str:
    return _add_months(_month_key(value), -1)


def _to_dicts(rows: Iterable[object]) -> list[dict]:
    payload: list[dict] = []
    for row in rows:
        if is_dataclass(row):
            payload.append(asdict(row))
        else:
            payload.append(dict(row))
    return payload


@st.cache_data(show_spinner=False)
def _load_context():
    return build_context()


def _filter_licenses(ctx, vendor: str, sku: str, seat_type: str, department: str) -> list[dict]:
    rows: list[dict] = []
    for row in ctx.licenses:
        if vendor != "All" and row.get("vendor") != vendor:
            continue
        if sku != "All" and row.get("sku") != sku:
            continue
        if seat_type != "All" and row.get("seat_type") != seat_type:
            continue
        if department != "All" and row.get("department") != department:
            continue
        rows.append(row)
    return rows


def _capacity_for_month(ctx, month: str, vendor: str, sku: str, seat_type: str) -> int:
    """
    Contracted seats aggregated to the active filter level.
    All:                  sum across everything active that month
    vendor only:          sum across all SKUs for that vendor
    vendor+SKU:           sum across all seat_types for that combo
    vendor+SKU+seat_type: exact seats for that combination
    Department filter has no contract data - always aggregates to
    SKU level max. Returns 0 if no active OF covers this month.
    """
    month_start = date.fromisoformat(f"{month}-01")
    group_max: dict[tuple[str, str, str], int] = {}
    for row in ctx.contract_history:
        row_vendor = str(row.get("vendor") or "")
        row_sku = str(row.get("sku") or "")
        row_seat = str(row.get("seat_type") or "")
        if vendor != "All" and row_vendor != vendor:
            continue
        if sku != "All" and row_sku != sku:
            continue
        if seat_type != "All" and row_seat != seat_type:
            continue
        start = _as_date(row.get("contract_start"))
        expiry = _as_date(row.get("contract_expiry"))
        if start is None or expiry is None:
            continue
        if not (start <= month_start < expiry):
            continue
        group_key = (row_vendor, row_sku, row_seat)
        seats = int(row.get("effective_total_seats") or 0)
        if group_key not in group_max or seats > group_max[group_key]:
            group_max[group_key] = seats
    return sum(group_max.values())


def _historical_lines(ctx, licenses: list[dict], vendor: str, sku: str, seat_type: str) -> pd.DataFrame:
    effective_months = [
        _month_key(effective)
        for row in licenses
        if (effective := _as_date(row.get("effective_license_date"))) is not None
    ]
    exit_lookup = {row.get("employee_id"): row for row in ctx.exited_employees}
    ghost_exit_months = []
    for row in licenses:
        if row.get("license_status") != "ghost":
            continue
        exit_row = exit_lookup.get(row.get("employee_id"))
        if exit_row is None:
            continue
        exit_date = _as_date(exit_row.get("exit_date"))
        if exit_date is not None:
            ghost_exit_months.append(_month_key(exit_date))

    if not effective_months and not ghost_exit_months:
        return pd.DataFrame(
            columns=[
                "month",
                "procurement_momentum",
                "vendor_billed_active",
                "productive_active",
                "ghost_accumulation",
                "contracted_capacity",
            ]
        )

    start_month = min([*effective_months, *ghost_exit_months])
    audit_month = _month_key(date.fromisoformat(ctx.audit_date))
    months = _month_range(start_month, audit_month)

    rows = []
    for month in months:
        procurement = 0
        billed = 0
        productive = 0
        for row in licenses:
            effective = _as_date(row.get("effective_license_date"))
            if effective is None or _month_key(effective) > month:
                continue
            procurement += 1
            status = row.get("license_status")
            if status != "deprovisioned":
                billed += 1
            if status not in {"ghost", "deprovisioned"}:
                productive += 1
        ghosts = sum(1 for ghost_month in ghost_exit_months if ghost_month <= month)
        rows.append(
            {
                "month": month,
                "procurement_momentum": procurement,
                "vendor_billed_active": billed,
                "productive_active": productive,
                "ghost_accumulation": ghosts,
                "contracted_capacity": _capacity_for_month(ctx, month, vendor, sku, seat_type),
            }
        )
    return pd.DataFrame(rows)


def _forecast_end_month(ctx, vendor: str, sku: str, seat_type: str) -> str:
    audit_month = _month_key(date.fromisoformat(ctx.audit_date))
    expiries: list[date] = []
    for row in ctx.contract_history:
        row_vendor = str(row.get("vendor") or "")
        row_sku = str(row.get("sku") or "")
        row_seat = str(row.get("seat_type") or "")
        if vendor != "All" and row_vendor != vendor:
            continue
        if sku != "All" and row_sku != sku:
            continue
        if seat_type != "All" and row_seat != seat_type:
            continue
        expiry = _as_date(row.get("contract_expiry"))
        if expiry is not None and _previous_month(expiry) >= audit_month:
            expiries.append(expiry)
    if not expiries:
        return _add_months(audit_month, 23)
    return _previous_month(max(expiries))


def _productive_active_count(licenses: list[dict]) -> int:
    return sum(1 for row in licenses if row.get("license_status") not in {"ghost", "deprovisioned"})


def _hire_counts_frame(ctx, department: str) -> pd.DataFrame:
    rows: list[dict] = []
    for hire in ctx.future_hires:
        if department != "All" and hire.get("department") != department:
            continue
        hire_date = _as_date(hire.get("hire_date"))
        if hire_date is None:
            continue
        rows.append({"month": _month_key(hire_date), "monthly_hires": 1})
    if not rows:
        return pd.DataFrame(columns=["month", "monthly_hires"])
    return pd.DataFrame(rows).groupby("month", as_index=False).agg(monthly_hires=("monthly_hires", "sum"))


def _active_demand_frame(rows: list[object]) -> pd.DataFrame:
    return pd.DataFrame(_to_dicts(rows))


def _aggregate_forecast_lines(
    momentum_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    hire_counts_df: pd.DataFrame,
    productive_active_baseline: int,
) -> pd.DataFrame:
    frames = []
    if not momentum_df.empty and "forecast_cumulative" in momentum_df.columns:
        frames.append(
            momentum_df.groupby("month", as_index=False)
            .agg(
                procurement_momentum_forecast=("forecast_cumulative", "sum"),
                procurement_monthly_new=("forecast_monthly_new", "sum"),
                confidence_lower=("confidence_lower", "sum"),
                confidence_upper=("confidence_upper", "sum"),
            )
        )
    if not demand_df.empty:
        demand = (
            demand_df.groupby("forecast_month", as_index=False)
            .agg(
                monthly_expected_new_licenses=("expected_new_licenses", "sum"),
                pipeline_data_available=("pipeline_data_available", "max"),
            )
            .rename(columns={"forecast_month": "month"})
        )
        frames.append(demand)
    if not hire_counts_df.empty:
        frames.append(hire_counts_df)
    if not frames:
        return pd.DataFrame()
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="month", how="outer")
    merged = merged.sort_values("month")
    if "monthly_hires" in merged.columns:
        merged["monthly_hires"] = merged["monthly_hires"].fillna(0).astype(int)
    if "monthly_expected_new_licenses" in merged.columns:
        monthly_expected = merged["monthly_expected_new_licenses"].fillna(0)
        merged["monthly_expected_new_licenses"] = monthly_expected.round(2)
        merged["cumulative_expected_new_licenses"] = monthly_expected.cumsum().round(2)
        merged["productive_active_demand_forecast"] = (
            productive_active_baseline + merged["cumulative_expected_new_licenses"]
        ).round(2)
    return merged


def _extend_forecast_to_month(
    forecast_df: pd.DataFrame,
    ctx,
    end_month: str,
    vendor: str,
    sku: str,
    seat_type: str,
    productive_active_baseline: int,
) -> pd.DataFrame:
    audit_month = _month_key(date.fromisoformat(ctx.audit_date))
    months = _month_range(audit_month, end_month)
    if not months:
        return forecast_df

    base = pd.DataFrame({"month": months})
    merged = base.merge(forecast_df, on="month", how="left")
    if "monthly_hires" not in merged.columns:
        merged["monthly_hires"] = 0
    if "monthly_expected_new_licenses" not in merged.columns:
        merged["monthly_expected_new_licenses"] = 0.0
    if "pipeline_data_available" not in merged.columns:
        merged["pipeline_data_available"] = False

    merged["monthly_hires"] = merged["monthly_hires"].fillna(0).astype(int)
    monthly_expected = merged["monthly_expected_new_licenses"].fillna(0.0)
    merged["monthly_expected_new_licenses"] = monthly_expected.round(2)
    merged["cumulative_expected_new_licenses"] = monthly_expected.cumsum().round(2)
    merged["productive_active_demand_forecast"] = (
        productive_active_baseline + merged["cumulative_expected_new_licenses"]
    ).round(2)
    merged["contracted_capacity"] = [
        _capacity_for_month(ctx, month, vendor, sku, seat_type) for month in merged["month"]
    ]
    merged["projected_over_capacity_seats"] = (
        merged["productive_active_demand_forecast"] - merged["contracted_capacity"]
    ).clip(lower=0).round(2)
    merged["projected_true_up"] = merged["projected_over_capacity_seats"] > 0
    return merged


def _combined_license_lines(historical_df: pd.DataFrame, forecast_df: pd.DataFrame) -> pd.DataFrame:
    if historical_df.empty and forecast_df.empty:
        return pd.DataFrame()
    combined = historical_df.copy()
    if "productive_active_demand_forecast" not in combined.columns:
        combined["productive_active_demand_forecast"] = pd.NA
    if "projected_over_capacity_seats" not in combined.columns:
        combined["projected_over_capacity_seats"] = pd.NA
    if "projected_true_up" not in combined.columns:
        combined["projected_true_up"] = False
    if not forecast_df.empty:
        forecast_columns = [
            "month",
            "procurement_momentum_forecast",
            "confidence_lower",
            "confidence_upper",
            "productive_active_demand_forecast",
            "contracted_capacity",
            "projected_over_capacity_seats",
            "projected_true_up",
        ]
        forecast_rows = forecast_df[
            [column for column in forecast_columns if column in forecast_df.columns]
        ].copy()
        combined = pd.concat([combined.dropna(axis=1, how="all"), forecast_rows], ignore_index=True, sort=False)
    return combined.sort_values("month")


def _filter_frame_year(df: pd.DataFrame, month_column: str, year_filter: str) -> pd.DataFrame:
    if year_filter == "All" or df.empty or month_column not in df.columns:
        return df
    return df[df[month_column].astype(str).str.startswith(f"{year_filter}-")]


ctx = _load_context()

all_vendors = sorted({row["vendor"] for row in ctx.contract_history} | {row["vendor"] for row in ctx.licenses})
active_license_vendors = sorted({row["vendor"] for row in ctx.licenses})

st.title("SaaS Forecast Inspector")
st.caption("Read-only dashboard over ProcessingContext and forecasting processor output.")

with st.sidebar:
    st.header("Filters")
    vendor = st.selectbox("Vendor", ["All", *all_vendors], index=0)
    vendor_rows = [row for row in ctx.licenses if vendor == "All" or row.get("vendor") == vendor]
    sku_options = sorted({row["sku"] for row in vendor_rows} | {row["sku"] for row in ctx.contract_history if vendor == "All" or row.get("vendor") == vendor})
    sku = st.selectbox("SKU", ["All", *sku_options], index=0)
    sku_rows = [row for row in vendor_rows if sku == "All" or row.get("sku") == sku]
    seat_options = sorted({row["seat_type"] for row in sku_rows} | {row["seat_type"] for row in ctx.contract_history if (vendor == "All" or row.get("vendor") == vendor) and (sku == "All" or row.get("sku") == sku)})
    seat_type = st.selectbox("Seat type", ["All", *seat_options], index=0)
    department = st.selectbox("Department", ["All", *sorted(ctx.known_departments)], index=0)
    known_years = sorted(
        {
            _month_key(value)[:4]
            for row in [*ctx.licenses, *ctx.future_hires]
            if (value := _as_date(row.get("effective_license_date") or row.get("hire_date"))) is not None
        }
        | {
            str(value.year)
            for row in ctx.contract_history
            for value in (_as_date(row.get("contract_start")), _as_date(row.get("contract_expiry")))
            if value is not None
        }
    )
    year_filter = st.selectbox("Year", ["All", *known_years], index=0)
    forecast_months = st.slider("Forecast horizon", min_value=3, max_value=24, value=24)

filtered_licenses = _filter_licenses(ctx, vendor, sku, seat_type, department)
historical_df = _historical_lines(ctx, filtered_licenses, vendor, sku, seat_type)

forecast_vendor = None if vendor == "All" else vendor
active_demand_df = _active_demand_frame(get_active_demand_history(ctx, vendor=forecast_vendor))
demand_rows = get_license_demand_forecast(
    ctx,
    vendor=forecast_vendor if forecast_vendor in active_license_vendors else None,
    department=None if department == "All" else department,
    forecast_months=forecast_months,
)
demand_df = pd.DataFrame(_to_dicts(demand_rows))

if sku != "All" and not active_demand_df.empty:
    active_demand_df = active_demand_df[active_demand_df["sku"] == sku]
if seat_type != "All" and not active_demand_df.empty:
    active_demand_df = active_demand_df[active_demand_df["seat_type"] == seat_type]
if sku != "All" and not demand_df.empty:
    demand_df = demand_df[demand_df["sku"] == sku]
if seat_type != "All" and not demand_df.empty:
    demand_df = demand_df[demand_df["seat_type"] == seat_type]

hire_counts_df = _hire_counts_frame(ctx, department)
productive_active_baseline = _productive_active_count(filtered_licenses)
forecast_lines_df = _aggregate_forecast_lines(
    active_demand_df,
    demand_df,
    hire_counts_df,
    productive_active_baseline,
)
forecast_end_month = _forecast_end_month(ctx, vendor, sku, seat_type)
forecast_lines_df = _extend_forecast_to_month(
    forecast_lines_df,
    ctx,
    forecast_end_month,
    vendor,
    sku,
    seat_type,
    productive_active_baseline,
)
combined_license_df = _combined_license_lines(historical_df, forecast_lines_df)

historical_df = _filter_frame_year(historical_df, "month", year_filter)
active_demand_df = _filter_frame_year(active_demand_df, "month", year_filter)
demand_df = _filter_frame_year(demand_df, "forecast_month", year_filter)
forecast_lines_df = _filter_frame_year(forecast_lines_df, "month", year_filter)
combined_license_df = _filter_frame_year(combined_license_df, "month", year_filter)

metric_cols = st.columns(5)
metric_cols[0].metric("Filtered licenses", f"{len(filtered_licenses):,}")
metric_cols[1].metric("Ghost licenses", f"{sum(1 for row in filtered_licenses if row.get('license_status') == 'ghost'):,}")
metric_cols[2].metric("Productive active", f"{productive_active_baseline:,}")
metric_cols[3].metric("Active demand rows", f"{len(active_demand_df):,}")
metric_cols[4].metric("Demand rows", f"{len(demand_df):,}")

true_up_months = forecast_lines_df[forecast_lines_df.get("projected_true_up", False) == True] if not forecast_lines_df.empty else pd.DataFrame()
first_true_up_month = true_up_months["month"].iloc[0] if not true_up_months.empty else "None"
st.metric("Projected true-up month", first_true_up_month)

st.subheader("License Decomposition and Demand Forecast")
if combined_license_df.empty:
    st.info("No historical license rows match the current filter.")
else:
    history_chart_columns = [
        column
        for column in [
            "procurement_momentum",
            "procurement_momentum_forecast",
            "vendor_billed_active",
            "productive_active",
            "productive_active_demand_forecast",
            "confidence_lower",
            "confidence_upper",
            "ghost_accumulation",
            "contracted_capacity",
        ]
        if column in combined_license_df.columns
    ]
    history_chart = combined_license_df.set_index("month")[history_chart_columns]
    st.line_chart(history_chart, height=380)
    st.dataframe(combined_license_df.tail(24), use_container_width=True, hide_index=True)

st.subheader("Forecast Lines")
if forecast_lines_df.empty:
    st.info("No forecast rows match the current filter.")
else:
    forecast_chart_columns = [
        column
        for column in [
            "procurement_momentum_forecast",
            "confidence_lower",
            "confidence_upper",
            "productive_active_demand_forecast",
        ]
        if column in forecast_lines_df.columns
    ]
    st.line_chart(forecast_lines_df.set_index("month")[forecast_chart_columns], height=340)
    st.dataframe(forecast_lines_df, use_container_width=True, hide_index=True)

left, right = st.columns(2)

with left:
    st.subheader("Active Demand History")
    if active_demand_df.empty:
        st.info("No active demand history rows match the current filter.")
    else:
        st.dataframe(active_demand_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("Hire-Driven Demand Forecast")
    if demand_df.empty:
        st.info("No demand forecast rows match the current filter.")
    else:
        display_cols = [
            "vendor",
            "sku",
            "seat_type",
            "forecast_month",
            "expected_new_licenses",
            "pipeline_data_available",
            "rate_grain_applied",
            "exit_model_applied",
        ]
        st.dataframe(demand_df[display_cols], use_container_width=True, hide_index=True)

st.subheader("Demand Detail by Department")
if demand_df.empty:
    st.info("No demand detail available for the current filter.")
else:
    detail_rows = []
    for row in demand_df.to_dict("records"):
        for detail in row.get("by_department", []):
            detail_rows.append(
                {
                    "vendor": row["vendor"],
                    "sku": row["sku"],
                    "seat_type": row["seat_type"],
                    "forecast_month": row["forecast_month"],
                    "pipeline_data_available": row["pipeline_data_available"],
                    **detail,
                }
            )
    if detail_rows:
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Selected months have no known hire-pipeline department detail.")
