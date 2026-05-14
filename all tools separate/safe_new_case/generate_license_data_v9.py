"""
Enterprise SaaS License & Churn Engine — Data Generator v9
=============================================================
20,000 rows | Jan 2024 – Mar 2026 (27 months) | Ref: 2026-04-02

Key changes from v8:
  - days_to_renewal    : floored at 0 — no negative values for expired contracts
  - contract_status    : new column — Active / Renewed / Lapsed
                         Active  → latest cycle, renewal_date >= 2026-04-02
                         Renewed → a higher license_cycle row exists for user_id
                         Lapsed  → latest cycle, renewal_date < 2026-04-02, no renewal
"""

import csv
import math
import random
from datetime import date, timedelta
import calendar

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
TARGET_ROWS  = 20000
RANDOM_SEED  = 42
OUTPUT_FILE  = f"license_data_v9_{TARGET_ROWS}.csv"
# ─────────────────────────────────────────────

random.seed(RANDOM_SEED)

REFERENCE_DATE    = date(2026, 4, 2)
START_MONTH       = date(2024, 1, 1)
NUM_MONTHS        = 27        # Jan 2024 → Mar 2026 inclusive
DATA_END          = date(2026, 3, 31)

VENDOR_PILLARS = {
    "vendor_1": ["Product", "Design", "Engineering", "Marketing"],
    "vendor_2": ["Legal", "Operations", "Engineering", "Finance"],
}

PILLAR_ROLES = {
    "Engineering": ["Software Engineer", "SRE", "Data Engineer", "DevOps Engineer"],
    "Design":      ["UI/UX Designer", "Brand Designer", "Product Designer"],
    "Product":     ["Product Manager", "Product Analyst"],
    "Marketing":   ["Marketing Specialist"],
    "Legal":       ["Legal Counsel"],
    "Operations":  ["Operations Analyst"],
    "Finance":     ["Finance Manager"],
}

USER_TYPES     = ["Full", "Editor", "Viewer", "Guest"]
HIGH_TIER      = {"Full", "Editor", "Developer"}
LOW_TIER       = {"Viewer", "Guest"}
NON_VIEWER     = {"Full", "Editor", "Developer", "Guest"}

RENEWAL_RATE        = 0.97   # 97% renew
EDITOR_UPGRADE_RATE = 0.20   # 20% of renewing Editors → Developer

# ── Helpers ───────────────────────────────────

def safe_date(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def month_date(offset):
    m = START_MONTH.month - 1 + offset
    return date(START_MONTH.year + m // 12, m % 12 + 1, 1)


def days_in_month(d):
    if d.month == 12:
        return 31
    return (date(d.year, d.month + 1, 1) - date(d.year, d.month, 1)).days


def rand_date_in_month(month_start):
    return month_start + timedelta(days=random.randint(0, days_in_month(month_start) - 1))


def rand_date(start, end):
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def compute_renewal_date(license_start):
    """Next 1-year anniversary of license_start."""
    return safe_date(license_start.year + 1, license_start.month, license_start.day)


def compute_health_score(days_since_login, documents_edited, days_active_in_period):
    """
    Period-scoped health score 0–100.
    Recency   50%: hard grace 30 days, then exponential decay
    Intensity 30%: log-saturated edits
    Velocity  20%: edits per active day (uses days_active_in_period)
    """
    # Recency
    if days_since_login <= 30:
        recency_score = 100.0
    else:
        recency_score = math.exp(-(days_since_login - 30) / 30.0) * 100

    # Intensity
    intensity_score = (math.log1p(documents_edited) / math.log1p(120)) * 100

    # Velocity — edits per active day, capped at 1/day = 100pts
    dap = max(1, days_active_in_period)
    velocity_score = min((documents_edited / dap) * 100, 100)

    score = (0.50 * recency_score +
             0.30 * intensity_score +
             0.20 * velocity_score)
    return round(score, 2)


def health_segment(score):
    if score >= 70:
        return "Healthy"
    elif score >= 30:
        return "Low Usage"
    else:
        return "At Risk"


def usage_for_type(user_type):
    """Generate baseline docs_edited and doc_views by user type."""
    if user_type == "Developer":
        return random.randint(60, 120), random.randint(150, 500)
    elif user_type in {"Full", "Editor"}:
        return random.randint(15, 120), random.randint(50, 500)
    else:  # Viewer, Guest
        return random.randint(0, 3), random.randint(0, 100)


# ── Step 1: Monthly base-user distribution ────

def build_monthly_counts(n_base_users):
    """
    Distribute n_base_users across 27 months with growth + seasonality.
    Returns list of counts summing to exactly n_base_users.
    """
    base = n_base_users / NUM_MONTHS
    raw  = []
    for i in range(NUM_MONTHS):
        growth    = 1.04 ** i
        noise     = random.uniform(0.97, 1.03)
        variation = random.uniform(0.85, 1.15)
        raw.append(base * growth * noise * variation)

    # Seasonal spikes: one Q1, one Q3 per calendar year (2024 & 2025)
    for group in [[0,1,2],[6,7,8],[12,13,14],[18,19,20]]:
        raw[random.choice(group)] *= random.uniform(1.15, 1.25)

    # Scale to exact total
    scale  = n_base_users / sum(raw)
    scaled = [max(1, round(v * scale)) for v in raw]

    diff = n_base_users - sum(scaled)
    for idx in random.sample(range(NUM_MONTHS), abs(diff)):
        scaled[idx] += 1 if diff > 0 else -1
        scaled[idx]  = max(1, scaled[idx])

    while sum(scaled) != n_base_users:
        d = n_base_users - sum(scaled)
        scaled[random.randint(0, NUM_MONTHS-1)] += 1 if d > 0 else -1

    return scaled


# ── Step 2: Build a base user record ──────────

def make_base_user(uid_int, month_start, inactive_set):
    """Generate one original license row (license_cycle=1)."""
    vendor    = random.choice(["vendor_1", "vendor_2"])
    pillar    = random.choice(VENDOR_PILLARS[vendor])
    role      = random.choice(PILLAR_ROLES[pillar])
    user_type = random.choices(USER_TYPES, weights=[25, 30, 30, 15], k=1)[0]

    hire_date          = rand_date(date(2018, 1, 1), date(2025, 12, 31))
    license_start_date = rand_date_in_month(month_start)

    if hire_date >= license_start_date:
        hire_date = max(date(2018, 1, 1),
                        license_start_date - timedelta(days=random.randint(1, 365)))

    is_active  = 0 if uid_int in inactive_set else 1
    renewal_dt = compute_renewal_date(license_start_date)

    # last_active_date scoped to this period
    period_end = min(renewal_dt, REFERENCE_DATE)

    if is_active == 0:
        churn_min        = license_start_date + timedelta(days=60)
        churn_max        = period_end
        if churn_min > churn_max:
            churn_min    = license_start_date + timedelta(days=1)
        last_active_date = rand_date(churn_min, churn_max)
    else:
        # Active window clamped to period_end so days_since stays >= 0
        active_window_start = max(license_start_date + timedelta(days=1),
                                  period_end - timedelta(days=45))
        active_window_end   = period_end
        if active_window_start >= active_window_end:
            active_window_start = license_start_date + timedelta(days=1)
        last_active_date = rand_date(active_window_start, active_window_end)

    # Guarantee ordering
    if license_start_date >= last_active_date:
        last_active_date = license_start_date + timedelta(days=random.randint(1, 14))
        last_active_date = min(last_active_date, period_end)

    # Hard guarantee: last_active_date never exceeds period_end
    last_active_date = min(last_active_date, period_end)
    days_since       = max(0, (period_end - last_active_date).days)
    days_active       = max(1, (last_active_date - license_start_date).days)
    docs_edited, doc_views = usage_for_type(user_type)
    days_to_renewal   = max(0, (renewal_dt - REFERENCE_DATE).days)

    h_score   = compute_health_score(days_since, docs_edited, days_active)
    h_segment = health_segment(h_score)

    return {
        "user_id":               f"U{uid_int+1:05d}",
        "is_active":             is_active,
        "pillar_name":           pillar,
        "hire_date":             hire_date.strftime("%Y-%m-%d"),
        "position_name":         role,
        "job_family_name":       pillar,
        "user_type":             user_type,
        "license_start_date":    license_start_date.strftime("%Y-%m-%d"),
        "last_active_date":      last_active_date.strftime("%Y-%m-%d"),
        "days_since_last_login": days_since,
        "documents_edited":      docs_edited,
        "document_views":        doc_views,
        "renewal_date":          renewal_dt.strftime("%Y-%m-%d"),
        "days_to_renewal":       days_to_renewal,
        "health_score":          h_score,
        "health_segment":        h_segment,
        "license_cycle":         1,
        "is_renewal":            0,
        "days_active_in_period": days_active,
        "tool":                  vendor,
    }


# ── Step 3: Build a renewal row ───────────────

def make_renewal_row(prev_row, cycle):
    """
    Generate a renewal row from a previous cycle row.
    license_start_date = prev renewal_date
    user_type: Editor has 20% chance to upgrade to Developer
    days_since_last_login: period-scoped
    """
    prev_renewal  = date.fromisoformat(prev_row["renewal_date"])
    new_start     = prev_renewal
    new_renewal   = compute_renewal_date(new_start)

    # Only create renewal if it starts within data window
    if new_start > DATA_END:
        return None

    # Editor → Developer upgrade
    user_type = prev_row["user_type"]
    if user_type == "Editor" and random.random() < EDITOR_UPGRADE_RATE:
        user_type = "Developer"

    period_end      = min(new_renewal, REFERENCE_DATE)
    window_start    = REFERENCE_DATE - timedelta(days=45)

    active_window_start = max(new_start + timedelta(days=1),
                              period_end - timedelta(days=45))
    active_window_end   = period_end
    if active_window_start >= active_window_end:
        active_window_start = new_start + timedelta(days=1)
    last_active_date = rand_date(active_window_start, active_window_end)

    if new_start >= last_active_date:
        last_active_date = new_start + timedelta(days=random.randint(1, 14))

    # Hard guarantee: never exceeds period_end
    last_active_date = min(last_active_date, period_end)
    days_since       = max(0, (period_end - last_active_date).days)
    days_active   = max(1, (last_active_date - new_start).days)
    days_to_renew = max(0, (new_renewal - REFERENCE_DATE).days)

    docs_edited, doc_views = usage_for_type(user_type)

    h_score   = compute_health_score(days_since, docs_edited, days_active)
    h_segment = health_segment(h_score)

    return {
        "user_id":               prev_row["user_id"],
        "is_active":             1,
        "pillar_name":           prev_row["pillar_name"],
        "hire_date":             prev_row["hire_date"],
        "position_name":         prev_row["position_name"],
        "job_family_name":       prev_row["job_family_name"],
        "user_type":             user_type,
        "license_start_date":    new_start.strftime("%Y-%m-%d"),
        "last_active_date":      last_active_date.strftime("%Y-%m-%d"),
        "days_since_last_login": days_since,
        "documents_edited":      docs_edited,
        "document_views":        doc_views,
        "renewal_date":          new_renewal.strftime("%Y-%m-%d"),
        "days_to_renewal":       days_to_renew,
        "health_score":          h_score,
        "health_segment":        h_segment,
        "license_cycle":         cycle,
        "is_renewal":            1,
        "days_active_in_period": days_active,
        "tool":                  prev_row["tool"],
    }


# ── Step 4: Apply anomaly overrides ──────────

def apply_anomalies(rows):
    """
    Pool A : 8% of Full users   → documents_edited=0, views 0–4
    Pool B : 5% of Editor users → documents_edited=0, views 0–9
    Pool C : 5% of Developer    → documents_edited=0, views 0–9
    All non-Viewer 0-edit users → At Risk hard cap
    """
    def get_pool(user_type_filter):
        return [i for i, r in enumerate(rows) if r["user_type"] == user_type_filter]

    for utype, rate, view_max in [("Full", 0.08, 4),
                                   ("Editor", 0.05, 9),
                                   ("Developer", 0.05, 9)]:
        pool = get_pool(utype)
        n    = round(len(pool) * rate)
        for idx in random.sample(pool, min(n, len(pool))):
            rows[idx]["documents_edited"] = 0
            rows[idx]["document_views"]   = random.randint(0, view_max)

    # Enforce At Risk for all non-Viewer 0-edit users
    for row in rows:
        if row["user_type"] != "Viewer" and row["documents_edited"] == 0:
            dap   = max(1, row["days_active_in_period"])
            score = compute_health_score(row["days_since_last_login"], 0, dap)
            row["health_score"]   = round(min(score, 29.9), 2)
            row["health_segment"] = "At Risk"


    # ── Post-process: derive contract_status per row ──────────────────────
    # Group rows by user_id to check if a higher cycle exists
    from collections import defaultdict
    user_max_cycle = defaultdict(int)
    for row in rows:
        uid = row["user_id"]
        if row["license_cycle"] > user_max_cycle[uid]:
            user_max_cycle[uid] = row["license_cycle"]

    for row in rows:
        uid        = row["user_id"]
        cycle      = row["license_cycle"]
        max_cycle  = user_max_cycle[uid]
        rn         = date.fromisoformat(row["renewal_date"])

        if cycle < max_cycle:
            # A higher cycle exists — this period was successfully renewed
            row["contract_status"] = "Renewed"
        elif rn >= REFERENCE_DATE:
            # Latest cycle, contract still active (not yet expired)
            row["contract_status"] = "Active"
        else:
            # Latest cycle but renewal date already passed with no renewal row
            row["contract_status"] = "Lapsed"

    return rows


# ── Step 5: Main generation loop ──────────────

def generate_rows():
    """
    Strategy:
    1. Estimate base users needed (~13,500) to hit 20k after renewals
    2. Generate base rows
    3. Generate renewal rows (cycle 2 & 3) for eligible users
    4. Trim or pad to exactly 20,000
    5. Apply anomalies
    6. Assign entry_id
    """
    # Estimate: average ~1.45 rows per user (base + ~45% get renewal)
    n_base = 13500
    monthly_counts = build_monthly_counts(n_base)

    # Inactive set: 3–5% of base users
    inactive_rate = random.uniform(0.03, 0.05)
    inactive_set  = set(random.sample(range(n_base), round(n_base * inactive_rate)))

    # Generate base rows
    rows        = []
    uid_counter = 0

    for month_offset, count in enumerate(monthly_counts):
        month_start = month_date(month_offset)
        for _ in range(count):
            row = make_base_user(uid_counter, month_start, inactive_set)
            rows.append(row)
            uid_counter += 1

    # Generate renewal rows
    renewal_rows   = []
    lapsed_indices = []   # base rows that will not renew

    for i, row in enumerate(rows):
        renewal_dt = date.fromisoformat(row["renewal_date"])

        # Only eligible if renewal falls within data window
        if renewal_dt > DATA_END:
            continue

        if random.random() < RENEWAL_RATE:
            r2 = make_renewal_row(row, cycle=2)
            if r2:
                renewal_rows.append(r2)

                # Check for second renewal
                r2_renewal = date.fromisoformat(r2["renewal_date"])
                if r2_renewal <= DATA_END:
                    if random.random() < RENEWAL_RATE:
                        r3 = make_renewal_row(r2, cycle=3)
                        if r3:
                            renewal_rows.append(r3)
        else:
            # Mark original as lapsed (non-renewal)
            lapsed_indices.append(i)

    # Mark lapsed rows
    for i in lapsed_indices:
        rows[i]["is_active"] = 0

    # Combine all rows
    all_rows = rows + renewal_rows
    random.shuffle(all_rows)   # mix cycles so CSV isn't sorted by cycle

    # Trim or pad to exactly TARGET_ROWS
    if len(all_rows) > TARGET_ROWS:
        all_rows = all_rows[:TARGET_ROWS]
    else:
        # Pad by duplicating renewal-eligible rows with new renewal entries
        while len(all_rows) < TARGET_ROWS:
            donor = random.choice([r for r in all_rows if r["license_cycle"] >= 1])
            pad   = make_renewal_row(donor, cycle=donor["license_cycle"] + 1)
            if pad:
                all_rows.append(pad)

    # Sort by license_start_date for readability then apply anomalies
    all_rows = apply_anomalies(all_rows)

    # Assign sequential entry_id
    for i, row in enumerate(all_rows):
        row["entry_id"] = f"E{i+1:05d}"

    return all_rows


# ── Step 6: Write CSV ─────────────────────────

FIELDNAMES = [
    "entry_id", "user_id", "is_active", "pillar_name",
    "hire_date", "position_name", "job_family_name",
    "user_type", "license_start_date", "last_active_date",
    "days_since_last_login", "documents_edited", "document_views",
    "renewal_date", "days_to_renewal", "health_score", "health_segment",
    "license_cycle", "is_renewal", "days_active_in_period", "tool",
    "contract_status",
]


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅  Written {len(rows):,} rows → {path}")


# ── Step 7: Validation ────────────────────────

def validate(rows):
    total         = len(rows)
    entry_ids     = [r["entry_id"] for r in rows]
    unique_users  = len(set(r["user_id"] for r in rows))
    renewals      = sum(1 for r in rows if r["is_renewal"] == 1)
    lapsed        = sum(1 for r in rows if r["is_active"] == 0 and r["is_renewal"] == 0)
    cycle2        = sum(1 for r in rows if r["license_cycle"] == 2)
    cycle3        = sum(1 for r in rows if r["license_cycle"] == 3)
    developers    = sum(1 for r in rows if r["user_type"] == "Developer")

    full_rows     = [r for r in rows if r["user_type"] == "Full"]
    editor_rows   = [r for r in rows if r["user_type"] == "Editor"]
    dev_rows      = [r for r in rows if r["user_type"] == "Developer"]

    full_0        = sum(1 for r in full_rows  if r["documents_edited"] == 0 and r["document_views"] <= 4)
    editor_0      = sum(1 for r in editor_rows if r["documents_edited"] == 0 and r["document_views"] <= 9)
    dev_0         = sum(1 for r in dev_rows   if r["documents_edited"] == 0 and r["document_views"] <= 9)

    seg           = {"Healthy": 0, "Low Usage": 0, "At Risk": 0}
    for r in rows:
        seg[r["health_segment"]] += 1

    renewal_soon  = sum(1 for r in rows if 0 <= r["days_to_renewal"] <= 60)

    # Date violations
    violations = 0
    for r in rows:
        h  = date.fromisoformat(r["hire_date"])
        ls = date.fromisoformat(r["license_start_date"])
        la = date.fromisoformat(r["last_active_date"])
        rn = date.fromisoformat(r["renewal_date"])
        if not (h < ls < la):
            violations += 1
        if r["days_since_last_login"] < 0:
            violations += 1
        if r["days_active_in_period"] < 1:
            violations += 1

    # Non-Viewer 0-edit At Risk check
    non_viewer_0_wrong = sum(
        1 for r in rows
        if r["user_type"] != "Viewer"
        and r["documents_edited"] == 0
        and r["health_segment"] != "At Risk"
    )

    print("\n── Validation Summary ────────────────────────────────")
    print(f"  Total rows              : {total:,}")
    print(f"  Unique entry_id         : {len(set(entry_ids)):,}")
    print(f"  Unique user_id          : {unique_users:,}")
    print(f"  Renewal rows (cycle 2)  : {cycle2:,}")
    print(f"  Renewal rows (cycle 3)  : {cycle3:,}")
    print(f"  Total is_renewal=1      : {renewals:,}")
    print(f"  Lapsed (non-renewal)    : {lapsed:,}")
    print(f"  Developer users         : {developers:,}")
    print(f"  Full users              : {len(full_rows):,}")
    print(f"  Editor users            : {len(editor_rows):,}")
    print(f"  Full 0-edit  (8% pool)  : {full_0:,}  ({full_0/max(1,len(full_rows))*100:.1f}%)")
    print(f"  Editor 0-edit (5% pool) : {editor_0:,}  ({editor_0/max(1,len(editor_rows))*100:.1f}%)")
    print(f"  Dev 0-edit   (5% pool)  : {dev_0:,}  ({dev_0/max(1,len(dev_rows))*100:.1f}% of {len(dev_rows)})")
    print(f"  Health Healthy          : {seg['Healthy']:,}  ({seg['Healthy']/total*100:.1f}%)")
    print(f"  Health Low Usage        : {seg['Low Usage']:,}  ({seg['Low Usage']/total*100:.1f}%)")
    print(f"  Health At Risk          : {seg['At Risk']:,}  ({seg['At Risk']/total*100:.1f}%)")
    print(f"  Renewal within 60 days  : {renewal_soon:,}")
    print(f"  Date/field violations   : {violations}")
    print(f"  Non-Viewer 0-edit wrong : {non_viewer_0_wrong}")

    status_counts = {"Active": 0, "Renewed": 0, "Lapsed": 0}
    for r in rows:
        status_counts[r["contract_status"]] += 1
    print(f"  Contract Active         : {status_counts['Active']:,}")
    print(f"  Contract Renewed        : {status_counts['Renewed']:,}")
    print(f"  Contract Lapsed         : {status_counts['Lapsed']:,}")

    # Verify no negative days_to_renewal
    neg_dtr = sum(1 for r in rows if r["days_to_renewal"] < 0)
    print(f"  Negative days_to_renewal: {neg_dtr}")
    print("──────────────────────────────────────────────────────\n")


# ── Main ─────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating {TARGET_ROWS:,} rows (v8)…")
    rows = generate_rows()
    validate(rows)
    write_csv(rows, OUTPUT_FILE)
