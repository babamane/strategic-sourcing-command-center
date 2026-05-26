"""Utility — append a new vendor row to vendor_overview_patched_v5.csv on GO verdict."""

import csv
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# ── Path resolution ────────────────────────────────────────────────────────────
# Resolve relative to this file:  sourcing 2/onboarding/backend/utils/csv_writer.py
#   → up 3 levels → sourcing 2/
#   → all tools separate/Saas_managment/data/uploads/vendor_overview_patched_v5.csv
_REPO_ROOT  = Path(__file__).resolve().parents[3]   # C:\sourcing 2
CSV_PATH    = _REPO_ROOT / "all tools separate" / "Saas_managment" / "data" / "uploads" / "vendor_overview_patched_v5.csv"

COLUMNS = [
    "of_id", "vendor", "sku", "seat_type", "contract_group_id",
    "contracted_seats", "unit_price", "contract_start", "contract_expiry",
    "notice_deadline", "auto_renewal", "true_down_rights", "measurement_method",
    "contract_status", "predecessor_of_id", "contract_event_type",
    "seat_delta", "effective_total_seats",
]


def _next_of_id(csv_path: Path) -> str:
    """Read all of_id values, parse the highest numeric suffix, increment by 1."""
    if not csv_path.exists():
        return "V1-OF-001"

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ids = [row.get("of_id", "") for row in reader if row.get("of_id")]

    # Extract numeric part from patterns like V1-OF-001, V3-OF-132
    max_num   = 0
    max_prefix = "V1-OF"
    for oid in ids:
        m = re.match(r"^(V\d+-OF)-(\d+)$", oid.strip())
        if m:
            n = int(m.group(2))
            if n > max_num:
                max_num    = n
                max_prefix = m.group(1)

    next_num = max_num + 1
    return f"{max_prefix}-{next_num:03d}"


def _contract_group_id(vendor: str, sku: str) -> str:
    """Generate a short contract-group slug from vendor + sku."""
    def abbrev(s: str) -> str:
        words = re.sub(r"[^a-zA-Z0-9 ]", "", s).split()
        return "".join(w[:3].upper() for w in words[:3])
    return f"{abbrev(vendor)}-{abbrev(sku)}-BASE"


def _parse_term_months(suggested_term: str) -> int:
    """Extract integer months from strings like '24 months', '1 year', '2 years'."""
    suggested_term = (suggested_term or "").lower()
    m = re.search(r"(\d+)[\s-]*month", suggested_term)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)[\s-]*year", suggested_term)
    if m:
        return int(m.group(1)) * 12
    return 12   # sensible default


def _fmt(dt: datetime) -> str:
    """Format as DD-MM-YYYY (same convention as existing rows)."""
    return dt.strftime("%d-%m-%Y")


def append_vendor_row(
    vendor_name: str,
    contract_data: dict,
    discovery_data: dict | None = None,
    csv_path: Path | None = None,
) -> dict:
    """
    Append one new row to vendor_overview_patched_v5.csv and return the row dict.

    Parameters
    ----------
    vendor_name   : raw vendor name from the onboarding session
    contract_data : ContractResult.model_dump() dict
    discovery_data: DiscoveryResult.model_dump() dict (optional, used for extra context)
    csv_path      : override the default CSV path (mainly for testing)
    """
    path = csv_path or CSV_PATH

    # ── Derive fields ──────────────────────────────────────────────────────────
    of_id = _next_of_id(path)

    # Vendor display name — prefer discovery company name if available
    vendor = vendor_name.strip().title()

    # SKU — build a meaningful label from discovery data
    # Priority: product name + short description > product name > business_model > generic
    sku = "Enterprise Platform"
    if discovery_data:
        products     = discovery_data.get("products") or []
        descriptions = discovery_data.get("product_descriptions") or {}
        biz_model    = (discovery_data.get("business_model") or "").strip()
        mkt_segment  = (discovery_data.get("market_segment") or "").strip()

        if products:
            primary = products[0].strip()
            desc    = descriptions.get(primary, "")
            # If description exists, extract a concise label (first 6 words max)
            if desc:
                short_desc = " ".join(desc.split()[:6]).rstrip(".,;:")
                sku = f"{primary} — {short_desc}"
            else:
                sku = primary
        elif biz_model and biz_model.lower() != "saas subscription":
            sku = biz_model
        elif mkt_segment:
            sku = f"{mkt_segment} Suite"

        sku = sku[:60]   # cap at 60 chars

    seat_type         = "Full"
    contract_group_id = _contract_group_id(vendor, sku)
    contracted_seats  = 0
    unit_price        = 0

    today   = datetime.today()
    months  = _parse_term_months(contract_data.get("suggested_term", ""))
    expiry  = today + timedelta(days=months * 30)
    notice  = expiry - timedelta(days=60)

    contract_start  = _fmt(today)
    contract_expiry = _fmt(expiry)
    notice_deadline = _fmt(notice)

    auto_renewal       = "TRUE"
    true_down_rights   = "FALSE"
    measurement_method = "snapshot"
    contract_status    = "active"
    predecessor_of_id  = ""
    contract_event_type = "new"
    seat_delta          = 0
    effective_total_seats = 0

    new_row = {
        "of_id":                 of_id,
        "vendor":                vendor,
        "sku":                   sku,
        "seat_type":             seat_type,
        "contract_group_id":     contract_group_id,
        "contracted_seats":      contracted_seats,
        "unit_price":            unit_price,
        "contract_start":        contract_start,
        "contract_expiry":       contract_expiry,
        "notice_deadline":       notice_deadline,
        "auto_renewal":          auto_renewal,
        "true_down_rights":      true_down_rights,
        "measurement_method":    measurement_method,
        "contract_status":       contract_status,
        "predecessor_of_id":     predecessor_of_id,
        "contract_event_type":   contract_event_type,
        "seat_delta":            seat_delta,
        "effective_total_seats": effective_total_seats,
    }

    # ── Append to CSV ──────────────────────────────────────────────────────────
    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_row)

    return new_row
