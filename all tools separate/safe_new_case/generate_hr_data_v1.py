"""
Synthetic HR Dataset Generator v3
=================================
14,298 rows | Reference Date: 2026-04-02

Creates a scaled Case 2 HR dataset that is intentionally separate from the
legacy 20k license dataset.
"""

import csv
import random
from collections import Counter, defaultdict
from datetime import date, timedelta


# CONFIG
ACTIVE_ROWS = 13344
FUTURE_ROWS = 954
TARGET_ROWS = ACTIVE_ROWS + FUTURE_ROWS
RANDOM_SEED = 42
REFERENCE_DATE = date(2026, 4, 2)
ACTIVE_END_DATE = date(2026, 3, 31)
ACTIVE_START_DATE = date(2018, 1, 1)
FUTURE_START_DATE = date(2026, 4, 1)
FUTURE_END_DATE = date(2026, 12, 31)
OUTPUT_FILE = "hr_data_v1.csv"

random.seed(RANDOM_SEED)


DEPT_WEIGHTS = {
    "Engineering": 40,
    "Marketing": 15,
    "Sales": 15,
    "Product": 10,
    "Operations": 10,
    "Finance": 5,
    "Legal": 5,
}

ROLE_MAP = {
    "Engineering": [
        "SRE",
        "Software Engineer",
        "Data Engineer",
        "DevOps",
    ],
    "Marketing": [
        "Marketing Specialist",
        "Brand Designer",
    ],
    "Sales": [
        "Account Executive",
        "Sales Development Representative",
        "Sales Operations Analyst",
    ],
    "Product": [
        "Product Manager",
        "Product Analyst",
    ],
    "Operations": [
        "Operations Analyst",
        "Program Coordinator",
        "Business Operations Manager",
    ],
    "Finance": [
        "Financial Analyst",
        "Finance Manager",
        "Procurement Analyst",
    ],
    "Legal": [
        "Legal Counsel",
        "Compliance Analyst",
        "Contract Manager",
    ],
}

LEVEL_WEIGHTS = {
    "L1": 5,
    "L2": 15,
    "L3": 30,
    "L4": 25,
    "L5": 15,
    "L6": 7,
    "L7": 3,
}

LEVEL_ORDER = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
LEVEL_TO_NUM = {level: idx + 1 for idx, level in enumerate(LEVEL_ORDER)}

# Role-level guardrails. This keeps junior titles away from exec ranges and
# mid/senior titles away from unrealistic entry levels.
ROLE_LEVEL_RANGES = {
    "SRE": ("L3", "L7"),
    "Software Engineer": ("L1", "L7"),
    "Data Engineer": ("L2", "L7"),
    "DevOps": ("L2", "L7"),
    "Marketing Specialist": ("L1", "L5"),
    "Brand Designer": ("L1", "L7"),
    "Account Executive": ("L2", "L7"),
    "Sales Development Representative": ("L1", "L3"),
    "Sales Operations Analyst": ("L2", "L5"),
    "Product Manager": ("L3", "L7"),
    "Product Analyst": ("L1", "L4"),
    "Operations Analyst": ("L1", "L4"),
    "Program Coordinator": ("L1", "L3"),
    "Business Operations Manager": ("L3", "L7"),
    "Financial Analyst": ("L1", "L4"),
    "Finance Manager": ("L3", "L7"),
    "Procurement Analyst": ("L1", "L4"),
    "Legal Counsel": ("L3", "L7"),
    "Compliance Analyst": ("L2", "L6"),
    "Contract Manager": ("L3", "L7"),
    "Senior Lead": ("L3", "L7"),
}


def daterange_months(start_date, end_date):
    months = []
    current = date(start_date.year, start_date.month, 1)
    while current <= end_date:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def month_end(month_start):
    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    return next_month - timedelta(days=1)


def rand_date(start_date, end_date):
    delta = (end_date - start_date).days
    if delta <= 0:
        return start_date
    return start_date + timedelta(days=random.randint(0, delta))


def weighted_choice(weight_map):
    options = list(weight_map.keys())
    weights = list(weight_map.values())
    return random.choices(options, weights=weights, k=1)[0]


def allowed_levels_for_role(role):
    min_level, max_level = ROLE_LEVEL_RANGES.get(role, ("L1", "L7"))
    min_idx = LEVEL_ORDER.index(min_level)
    max_idx = LEVEL_ORDER.index(max_level)
    return LEVEL_ORDER[min_idx:max_idx + 1]


def choose_level_for_role(role):
    allowed = set(allowed_levels_for_role(role))
    filtered = {level: weight for level, weight in LEVEL_WEIGHTS.items() if level in allowed}
    return weighted_choice(filtered)


def build_monthly_counts(total_rows, start_date, end_date, apply_growth):
    months = daterange_months(start_date, end_date)
    base = total_rows / len(months)
    raw = []

    for idx, month_start in enumerate(months):
        growth_multiplier = (1.04 ** idx) if apply_growth else 1.0
        seasonal_multiplier = 1.15 if month_start.month in {1, 2, 3, 7, 8, 9} else 1.0
        noise = random.uniform(0.97, 1.03)
        raw.append(base * growth_multiplier * seasonal_multiplier * noise)

    scale = total_rows / sum(raw)
    scaled = [max(1, round(value * scale)) for value in raw]

    while sum(scaled) != total_rows:
        diff = total_rows - sum(scaled)
        if diff > 0:
            scaled[random.randrange(len(scaled))] += 1
        else:
            idx = random.randrange(len(scaled))
            if scaled[idx] > 1:
                scaled[idx] -= 1

    return list(zip(months, scaled))


def make_employee(employee_num, status, hire_dt):
    dept = weighted_choice(DEPT_WEIGHTS)
    level = weighted_choice(LEVEL_WEIGHTS)
    eligible_roles = [role for role in ROLE_MAP[dept] if level in allowed_levels_for_role(role)]
    role = random.choice(eligible_roles) if eligible_roles else random.choice(ROLE_MAP[dept])
    if level not in allowed_levels_for_role(role):
        level = choose_level_for_role(role)

    return {
        "employee_id": f"U{employee_num:05d}",
        "pillar_dept": dept,
        "job_role": role,
        "job_level": level,
        "is_active": status,
        "hire_date": hire_dt.strftime("%Y-%m-%d"),
    }


def generate_active_rows(start_employee_num):
    rows = []
    employee_num = start_employee_num
    for month_start, count in build_monthly_counts(ACTIVE_ROWS, ACTIVE_START_DATE, ACTIVE_END_DATE, apply_growth=True):
        month_last_day = min(month_end(month_start), ACTIVE_END_DATE)
        for _ in range(count):
            hire_dt = rand_date(month_start, month_last_day)
            if hire_dt > ACTIVE_END_DATE:
                hire_dt = ACTIVE_END_DATE
            rows.append(make_employee(employee_num, "Active", hire_dt))
            employee_num += 1
    return rows, employee_num


def generate_future_rows(start_employee_num):
    rows = []
    employee_num = start_employee_num
    for month_start, count in build_monthly_counts(FUTURE_ROWS, FUTURE_START_DATE, FUTURE_END_DATE, apply_growth=False):
        month_last_day = min(month_end(month_start), FUTURE_END_DATE)
        for _ in range(count):
            hire_dt = rand_date(month_start, month_last_day)
            rows.append(make_employee(employee_num, "Future_Hire", hire_dt))
            employee_num += 1
    return rows


def validate_rows(rows):
    violations = []
    for row in rows:
        hire_dt = date.fromisoformat(row["hire_date"])
        if row["is_active"] == "Active" and hire_dt > REFERENCE_DATE:
            violations.append(f"Active hire_date in future for {row['employee_id']}")
        if row["is_active"] == "Future_Hire" and hire_dt < FUTURE_START_DATE:
            violations.append(f"Future_Hire before future window for {row['employee_id']}")
        if row["job_role"] == "Senior Lead" and row["job_level"] in {"L1", "L2"}:
            violations.append(f"Senior Lead mapped to invalid level for {row['employee_id']}")
        allowed = allowed_levels_for_role(row["job_role"])
        if row["job_level"] not in allowed:
            violations.append(f"Role-level mismatch for {row['employee_id']}")
    return violations


def print_summary(rows):
    status_counts = Counter(row["is_active"] for row in rows)
    dept_counts = Counter(row["pillar_dept"] for row in rows)

    level_totals = defaultdict(int)
    level_counts = defaultdict(int)
    for row in rows:
        level_totals[row["pillar_dept"]] += LEVEL_TO_NUM[row["job_level"]]
        level_counts[row["pillar_dept"]] += 1

    avg_levels = {
        dept: level_totals[dept] / level_counts[dept]
        for dept in DEPT_WEIGHTS
    }

    print("\nValidation Summary")
    print("------------------")
    print(f"Total Row Count           : {len(rows):,}")
    print("Breakdown Active Status   :")
    print(f"  Active                  : {status_counts['Active']:,}")
    print(f"  Future_Hire             : {status_counts['Future_Hire']:,}")
    print("Count per pillar_dept     :")
    for dept in DEPT_WEIGHTS:
        print(f"  {dept:<22} {dept_counts[dept]:,}")
    print("Average job_level by dept :")
    for dept in DEPT_WEIGHTS:
        print(f"  {dept:<22} {avg_levels[dept]:.2f}")

    violations = validate_rows(rows)
    print(f"Validation violations     : {len(violations)}")


def write_csv(rows, path):
    fieldnames = [
        "employee_id",
        "pillar_dept",
        "job_role",
        "job_level",
        "is_active",
        "hire_date",
    ]
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Written {len(rows):,} rows to {path}")


def main():
    active_rows, next_employee_num = generate_active_rows(start_employee_num=1)
    future_rows = generate_future_rows(start_employee_num=next_employee_num)
    rows = active_rows + future_rows
    random.shuffle(rows)
    rows.sort(key=lambda row: (row["hire_date"], row["employee_id"]))

    print_summary(rows)
    write_csv(rows, OUTPUT_FILE)


if __name__ == "__main__":
    main()
