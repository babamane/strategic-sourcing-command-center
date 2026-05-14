from email.mime.multipart import MIMEMultipart
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import sqlite3
from pathlib import Path
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from datetime import date, timedelta
import calendar
from case2_engine_v1 import is_case2_sourcing_request, handle_case2_query

# -------------------------------
# 🔧 CONFIG  (loaded from .env)
# -------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

BASE_DIR    = Path(__file__).resolve().parent
DATA_DIR    = BASE_DIR / "data"
SQLITE_PATH = DATA_DIR / os.getenv("SQLITE_DB_PATH", "saas_data.db")

PRICING_SQL = """
    CASE
        WHEN license_tier LIKE '%Full%' THEN 45
        WHEN license_tier LIKE '%Editor%' THEN 30
        WHEN license_tier LIKE '%Guest%' THEN 20
        WHEN license_tier LIKE '%Viewer%' THEN 10
        ELSE 0
    END
"""

KNOWN_VENDORS = ["vendor_1", "vendor_2", "vendor_3"]

OVERVIEW_REPORTS = {
    "vendor_1": {
        "title": "Vendor_1 Quarterly Summary Report",
        "url": "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/pallanti_vatsal_agivant_com/IQANHXtM3SogSIP06Wn7nNU-AVqW6VYBiKJIXYHkbdVkBYU?e=v06F4W",
        "body_summary": (
            "This summarized report gives an overview of forecasted demand, renewal exposure, "
            "at-risk users, and the overall budget and savings picture for vendor_1 for the reporting period."
        ),
    },
    "vendor_2": {
        "title": "Vendor_2 Quarterly Summary Report",
        "url": "https://agivantechnologiespvtltd-my.sharepoint.com/:w:/g/personal/pallanti_vatsal_agivant_com/IQAao0wgQaFzTrkJ4f8y7Fs5AZGbaYzbfY_54s4hzxwyi1g?e=2n6z8d",
        "body_summary": (
            "This summarized report gives an overview of forecasted demand, renewal exposure, "
            "at-risk users, and the overall budget and savings picture for vendor_2 for the reporting period."
        ),
    },
}

MONTH_MAP = {
    "may": "2026-05-01",
    "june": "2026-06-01",
    "jul": "2026-07-01",
    "july": "2026-07-01",
    "august":"2026-08-01",
}
# -------------------------------
# 🏷️  TIER DISPLAY ALIASES
# Map DB values → display names at the logical layer.
# Add more entries here without touching queries or DB.
# -------------------------------
TIER_ALIASES = {
    "Guest": "Contributor",
}

def apply_tier_aliases(df):
    """Rename license_tier values using TIER_ALIASES wherever the column exists."""
    if "license_tier" in df.columns:
        df = df.copy()
        df["license_tier"] = df["license_tier"].replace(TIER_ALIASES)
    return df



# -------------------------------
# 📅 QUARTER HELPERS  [NEW]
# -------------------------------

def get_upcoming_quarter_months() -> list[str]:
    """
    Returns the 3 month start-date strings for the NEXT calendar quarter
    relative to today's date.

    Quarters:
        Q1 → Jan, Feb, Mar
        Q2 → Apr, May, Jun
        Q3 → Jul, Aug, Sep
        Q4 → Oct, Nov, Dec
    """
    today = date.today()
    current_month = today.month          # 1-12
    current_year  = today.year

    # Determine which quarter we are currently in
    current_q = (current_month - 1) // 3  # 0,1,2,3

    # The NEXT quarter
    next_q = (current_q + 1) % 4
    next_q_year = current_year if next_q > 0 else current_year + 1

    # First month of next quarter (1-indexed)
    first_month = next_q * 3 + 1         # Q0→1, Q1→4, Q2→7, Q3→10

    months = []
    for offset in range(3):
        m = first_month + offset
        y = next_q_year
        if m > 12:
            m -= 12
            y += 1
        months.append(f"{y}-{m:02d}-01")

    return months


def get_next_month() -> list[str]:
    """
    Returns the ISO date string for the first day of next calendar month.
    e.g. today = April 19 2026  →  ['2026-05-01']
    """
    today = date.today()
    if today.month == 12:
        return [f"{today.year + 1}-01-01"]
    return [f"{today.year}-{today.month + 1:02d}-01"]


def is_quarter_request(message: str) -> bool:
    """Detect whether the user is asking about a quarter / upcoming quarter."""
    keywords = [
        "quarter", "q1", "q2", "q3", "q4",
        "next quarter", "upcoming quarter", "quarterly"
    ]
    msg = message.lower()
    return any(k in msg for k in keywords)


# -------------------------------
# 🔌 DB CONNECTION (SQLite)
# -------------------------------
def get_connection():
    """Return a fresh sqlite3 connection to saas_data.db."""
    return sqlite3.connect(SQLITE_PATH)


# -------------------------------
# 🔍 INTENT DETECTION
# -------------------------------
def detect_intent(message: str) -> str:
    msg = message.lower()
    if "overview" in msg:
        return "overview"
    if any(k in msg for k in ["mail", "email", "form"]):
        return "mail"
    if any(k in msg for k in ["forecast", "demand", "acquisition"]):
        return "forecast"
    if any(k in msg for k in ["summary", "overview"]):
        return "summary"
    if any(k in msg for k in ["budget", "cost", "spend", "net"]):
        return "budget"
    if any(k in msg for k in ["at risk", "at-risk", "inactive", "reclaim", "reclamation", "churn"]):
        return "at_risk"
    if any(k in msg for k in ["renewal", "split", "expiring", "contracts"]):
        return "renewal"
    if any(k in msg for k in ["saving", "savings", "potential"]):
        return "savings"
    return "general"


# -------------------------------
# 🏢 VENDOR EXTRACTION
# -------------------------------
def extract_vendor(message: str, history: list) -> str | None:
    msg = message.lower()
    for v in KNOWN_VENDORS:
        if v in msg:
            return v
    for turn in reversed(history):
        content = turn.get("content", "").lower()
        for v in KNOWN_VENDORS:
            if v in content:
                return v
    return None


# -------------------------------
# 📅 MONTH EXTRACTION  [ENHANCED]
# -------------------------------
def extract_months(message: str, history: list) -> list:
    """
    Supports:
      • Named months  ("May", "June", "July")
      • Quarter keywords ("upcoming quarter", "next quarter", "Q3")
    """
    # --- Quarter shortcut ---
    if is_quarter_request(message):
        return get_upcoming_quarter_months()

    msg = message.lower()
    found = []
    for key, val in MONTH_MAP.items():
        if key in msg:
            found.append(val)

    # Check history if nothing found in current message
    if not found:
        for turn in reversed(history):
            content = turn.get("content", "").lower()
            if is_quarter_request(content):
                return get_upcoming_quarter_months()
            for key, val in MONTH_MAP.items():
                if key in content and val not in found:
                    found.append(val)

    return list(dict.fromkeys(found))  # deduplicate, preserve order


def extract_splits(user_message: str) -> list:
    query = user_message.lower()
    splits = []
    if "department" in query or "pillar" in query:
        splits.append("department_pillar")
    if "job" in query or "role" in query or "position" in query:
        splits.append("job_position")
    return splits


# -------------------------------
# 📧 GOOGLE FORM EMAIL
# -------------------------------
def send_google_form_email(sender_email, sender_password, recipient_email, subject, form_url):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    body = f"""
    Hello,

    We've identified that one of your assigned licenses is at risk of being reclaimed due to low usage.

    License Details:
     Vendor: Vendor_1
     License Type: Full License
     Last Activity: 60 days ago
     User Engagement Score: 45.34 / 100

    To continue using this license, please provide the necessary details by completing the form below:

    {form_url}

    Your response will help us make informed decisions and optimize overall SaaS usage across the organization.

    Thank you for your cooperation.

    Best regards,
    SaaS Management Team
    """
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"Form link sent successfully to {recipient_email}!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_report_overview_email(
    sender_email,
    sender_password,
    recipient_email,
    subject,
    report_title,
    report_url,
    body_summary,
):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    # Use HTML for the body to support hyperlinks
    html_body = f"""
    <html>
      <body>
        <p>Hello,</p>
        <p>Please find the <strong>{report_title}</strong> link below.</p>
        <p>
          This email provides an overview of what we will read in the summarized report:<br>
          <em>{body_summary}</em>
        </p>
        <p>
          <strong>Access the report here:</strong> 
          <a href="{report_url}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">
            {report_title}
          </a>
        </p>
        <p>Best regards,<br>
        <strong>SAFE AI</strong></p>
      </body>
    </html>
    """
    
    # Crucial change: attach as 'html' instead of 'plain'
    message.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"Overview report email sent successfully to {recipient_email}!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def get_overview_report(vendor: str | None) -> dict:
    vendor_key = vendor if vendor in OVERVIEW_REPORTS else "vendor_1"
    return OVERVIEW_REPORTS[vendor_key]


def get_overview_report_url(vendor: str | None = None) -> str:
    return get_overview_report(vendor).get("url", "")


def get_overview_success_message(vendor: str | None = None) -> str:
    vendor_key = vendor if vendor in OVERVIEW_REPORTS else "vendor_1"
    return f"Overview mail has been sent for {vendor_key}."


# -------------------------------
# 📊 SQL QUERIES
# -------------------------------
def query_renewal(vendor: str, months: list) -> pd.DataFrame:
    month_filter = "', '".join(months)
    sql = f"""
    SELECT
        saas_tool,
        license_tier,
        renewal_due_month,
        SUM(projected_renewal_count) AS total_contracts_expiring,
        SUM(projected_renewal_count * ({PRICING_SQL})) AS renewal_liability_amount
    FROM fct_renewal_liability
    WHERE renewal_due_month IN ('{month_filter}')
        AND saas_tool = '{vendor}'
    GROUP BY license_tier, renewal_due_month
    ORDER BY renewal_due_month, license_tier;
    """
    conn = get_connection()
    result = apply_tier_aliases(pd.read_sql(sql, conn))
    conn.close()
    return result


def query_forecast(vendor: str, months: list, splits: list = None) -> pd.DataFrame:
    """
    Fetches forecast data with flexible grouping.
    """
    month_filter = "', '".join(months)
    allowed_splits = ["department_pillar", "job_position"]

    group_fields = []
    if splits:
        splits = [s for s in splits if s in allowed_splits]
        group_fields.extend(splits)
    group_fields.append("license_tier")
    group_fields.append("month_start_date")

    select_fields = ["saas_tool"] + group_fields
    select_clause = ",\n        ".join(select_fields)
    group_clause  = ", ".join(select_fields)
    order_clause  = ", ".join(group_fields)

    sql = f"""
    SELECT
        {select_clause},
        SUM(forecasted_new_acquisitions)                  AS forecasted_licenses,
        SUM(forecasted_new_acquisitions * ({PRICING_SQL})) AS forecasted_cost
    FROM fct_license_forecast
    WHERE month_start_date IN ('{month_filter}')
        AND saas_tool = '{vendor}'
    GROUP BY {group_clause}
    ORDER BY {order_clause};
    """
    conn = get_connection()
    result = apply_tier_aliases(pd.read_sql(sql, conn))
    conn.close()
    return result


def query_budget(vendor: str, months: list, splits: list = None) -> pd.DataFrame:
    """
    Returns a three-row-per-tier breakdown for each month.
    Compatible with SQLite — uses CASE WHEN instead of MySQL FIELD().
    """
    month_filter = "', '".join(months)
    allowed_splits = ["department_pillar", "job_position"]
    splits = [s for s in (splits or []) if s in allowed_splits]

    null_pads   = ",\n            ".join([f"NULL AS {s}" for s in splits])
    null_clause = f",\n            {null_pads}" if null_pads else ""
    
    split_cols      = (", ".join(splits) + ", ") if splits else ""
    split_group_by  = (", " + ", ".join(splits)) if splits else ""

    sql = f"""
    SELECT
        saas_tool,
        {split_cols}license_tier,
        month_start_date,
        cost_type,
        SUM(licenses) AS total_licenses,
        SUM(cost)     AS total_spend
    FROM (

        -- 1. New Acquisitions
        SELECT
            saas_tool{null_clause},
            license_tier,
            month_start_date,
            'New Acquisitions'                               AS cost_type,
            SUM(forecasted_new_acquisitions)                 AS licenses,
            SUM(forecasted_new_acquisitions * ({PRICING_SQL})) AS cost
        FROM fct_license_forecast
        WHERE month_start_date IN ('{month_filter}')
          AND saas_tool = '{vendor}'
        GROUP BY saas_tool, license_tier, month_start_date{split_group_by}

        UNION ALL

        -- 2. Renewals
        SELECT
            saas_tool{null_clause},
            license_tier,
            renewal_due_month                                AS month_start_date,
            'Renewals'                                       AS cost_type,
            SUM(projected_renewal_count)                     AS licenses,
            SUM(projected_renewal_count * ({PRICING_SQL}))   AS cost
        FROM fct_renewal_liability
        WHERE renewal_due_month IN ('{month_filter}')
          AND saas_tool = '{vendor}'
        GROUP BY saas_tool, license_tier, renewal_due_month{split_group_by}

        UNION ALL

        -- 3. Combined Total
        SELECT
            f.saas_tool{null_clause},
            f.license_tier                                   AS license_tier,
            f.month_start_date                               AS month_start_date,
            'Combined Total'                                 AS cost_type,
            SUM(f.forecasted_new_acquisitions) 
              + COALESCE(MAX(r.renewal_licenses), 0)         AS licenses,
            SUM(f.forecasted_new_acquisitions * ({PRICING_SQL})) 
              + COALESCE(MAX(r.renewal_cost), 0)             AS cost
        FROM fct_license_forecast f
        LEFT JOIN (
            SELECT
                saas_tool                                    AS r_saas_tool,
                license_tier                                 AS r_license_tier,
                renewal_due_month                            AS r_month,
                SUM(projected_renewal_count)                 AS renewal_licenses,
                SUM(projected_renewal_count * ({PRICING_SQL})) AS renewal_cost
            FROM fct_renewal_liability
            WHERE renewal_due_month IN ('{month_filter}')
              AND saas_tool = '{vendor}'
            GROUP BY saas_tool, license_tier, renewal_due_month
        ) r ON f.saas_tool    = r.r_saas_tool
           AND f.license_tier = r.r_license_tier
           AND f.month_start_date = r.r_month
        WHERE f.month_start_date IN ('{month_filter}')
          AND f.saas_tool = '{vendor}'
        GROUP BY f.saas_tool, f.license_tier, f.month_start_date{split_group_by}

    ) all_costs
    GROUP BY saas_tool, {split_cols}license_tier, month_start_date, cost_type
    ORDER BY {split_cols}license_tier, month_start_date,
             CASE cost_type
               WHEN 'New Acquisitions' THEN 1
               WHEN 'Renewals'         THEN 2
               ELSE 3
             END;
    """

    conn = get_connection()
    result = apply_tier_aliases(pd.read_sql(sql, conn))
    conn.close()
    return result


def query_at_risk(vendor: str) -> pd.DataFrame:
    sql = f"""
    SELECT
        user_id,
        saas_tool,
        license_tier,
        days_until_contract_renewal,
        days_since_last_activity,
        drop_reason_codes,
        {PRICING_SQL} AS potential_monthly_savings
    FROM stg_at_risk_pool
    WHERE saas_tool = '{vendor}'
    ORDER BY days_since_last_activity DESC
    LIMIT 10;
    """
    conn = get_connection()
    result = apply_tier_aliases(pd.read_sql(sql, conn))
    conn.close()
    return result


def query_savings(vendor: str) -> list:
    sql = f"""
    SELECT SUM({PRICING_SQL}) AS total,
           COUNT(*)           AS churn_user_count
    FROM stg_at_risk_pool
    WHERE saas_tool = '{vendor}'
    """
    conn = get_connection()
    result = pd.read_sql(sql, conn)
    conn.close()
    val  = result['total'].iloc[0]
    user = result['churn_user_count'].iloc[0]
    return [float(val) if val is not None else 0.0, user]


# -------------------------------
# 📦 CONTEXT BUILDER  [ENHANCED]
# -------------------------------
def build_context(intent: str, vendor: str, months: list, splits: list = None) -> str:
    context_parts = []

    if not splits:
        splits = []

    if not months:
        months = get_next_month()   # should be set by handle_query; safety fallback

    # ── MAIL ──────────────────────────────────────────────────────────────────
    if intent in ("mail", "send mail"):
        sender_email     = os.getenv("SENDER_EMAIL")
        sender_password  = os.getenv("SENDER_APP_PASSWORD")
        recipient_email  = os.getenv("RECIPIENT_EMAIL")
        google_form_link = os.getenv("GOOGLE_FORM_LINK")

        send_google_form_email(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_email=recipient_email,
            subject="Action Required: Please fill out this form",
            form_url=google_form_link,
        )
        return "Task executed. Email sent with Google Form link."

    if intent == "overview":
        sender_email    = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_APP_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")
        report_vendor   = vendor if vendor in OVERVIEW_REPORTS else "vendor_1"
        report          = get_overview_report(report_vendor)

        send_report_overview_email(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_email=recipient_email,
            subject=f"{report['title']} Overview",
            report_title=report["title"],
            report_url=report["url"],
            body_summary=report["body_summary"],
        )
        return get_overview_success_message(report_vendor)

    # ── FORECAST ──────────────────────────────────────────────────────────────
    if intent in ("forecast", "summary"):
        df = query_forecast(vendor, months, splits=splits)
        split_text = ", ".join(splits) if splits else "license_tier"
        label = f"[FORECAST / NEW DEMAND DATA for {vendor} | months: {', '.join(months)} | split by {split_text}]"

        if df.empty:
            context_parts.append(label + "\nNo data found for the selected months.")
        else:
            monthly_str = df.to_string(index=False)

            agg_group_cols = [c for c in ["saas_tool"] + splits + ["license_tier"] if c in df.columns]
            num_cols = ["forecasted_licenses", "forecasted_cost"]
            agg_df = (
                df.groupby(agg_group_cols)[num_cols]
                .sum()
                .reset_index()
            )
            agg_df["forecasted_licenses"] = agg_df["forecasted_licenses"].astype(int)
            agg_df["forecasted_cost"]     = agg_df["forecasted_cost"].astype(int)

            grand_licenses = int(agg_df["forecasted_licenses"].sum())
            grand_cost     = int(agg_df["forecasted_cost"].sum())

            period_label = (
                f"Q3 {months[0][:4]}" if len(months) == 3 and is_quarter_request("")
                else f"{len(months)}-month period"
            )

            agg_str = (
                f"\n[AGGREGATED TOTALS across all {len(months)} month(s) — REPORT BOTH licenses AND forecasted_cost PER TIER]\n"
                + agg_df.to_string(index=False)
                + f"\nGRAND TOTAL → {grand_licenses} licenses, ${grand_cost:,} forecasted cost"
            )

            context_parts.append(
                label
                + "\n\n--- Monthly Breakdown (for per-month detail only) ---\n"
                + monthly_str
                + "\n\n--- !! IMPORTANT: Use the aggregated totals below for any 'total' or 'quarterly' figures !! ---"
                + agg_str
            )

    # ── BUDGET  [ENHANCED] ────────────────────────────────────────────────────
    if intent == "budget":
        df = query_budget(vendor, months, splits=splits)
        split_text = ", ".join(splits) if splits else "license_tier"
        label = (
            f"[TOTAL BUDGET / SPEND FORECAST for {vendor} | "
            f"months: {', '.join(months)} | split by {split_text}]"
        )
        if not df.empty:
            monthly_str = df.to_string(index=False)

            agg_group_cols = [c for c in ["saas_tool"] + (splits or []) + ["license_tier"] if c in df.columns]
            agg_df = (
                df.groupby(agg_group_cols)[["total_licenses", "total_spend"]]
                .sum()
                .reset_index()
            )
            agg_df["total_licenses"] = agg_df["total_licenses"].astype(int)
            agg_df["total_spend"]    = agg_df["total_spend"].round(2)

            grand_licenses = int(agg_df["total_licenses"].sum())
            grand_spend    = float(agg_df["total_spend"].sum())

            agg_str = (
                f"\n[AGGREGATED BUDGET TOTALS across all {len(months)} month(s) — REPORT BOTH total_licenses AND total_spend PER TIER]\n"
                + agg_df.to_string(index=False)
                + f"\nGRAND TOTAL → {grand_licenses} licenses, ${grand_spend:,.2f} total spend"
            )

            context_parts.append(
                label
                + "\n\n--- Monthly Breakdown (for per-month detail only) ---\n"
                + monthly_str
                + "\n\n--- !! IMPORTANT: Use aggregated totals below for any total/quarterly figures !! ---"
                + agg_str
            )
        else:
            context_parts.append(label + "\nNo data found for the selected months.")

    # ── RENEWAL ───────────────────────────────────────────────────────────────
    if intent in ("renewal", "summary"):
        df = query_renewal(vendor, months)
        label = f"[RENEWAL LIABILITY DATA for {vendor}]"
        context_parts.append(
            label + "\n" + (df.to_string(index=False) if not df.empty else "No data found for the selected months.")
        )

    # ── AT-RISK ───────────────────────────────────────────────────────────────
    if intent in ("at_risk", "savings", "summary", "at risk", "at-risk"):
        df = query_at_risk(vendor)
        label = f"[AT-RISK USERS for {vendor}]"
        context_parts.append(
            label + "\n" + (df.to_string(index=False) if not df.empty else "No at-risk users found.")
        )

    # ── SAVINGS ───────────────────────────────────────────────────────────────
    if intent in ("budget", "summary") and intent != "forecast":
        total_savings = query_savings(vendor)
        context_parts.append(
            f"[TOTAL POTENTIAL SAVINGS for {vendor}]\n"
            f"${total_savings[0]:,.2f} in potential monthly savings "
            f"from reclaiming licenses of {total_savings[1]} churn users."
        )

    return "\n\n".join(context_parts)


# -------------------------------
# 🤖 GEMINI / OLLAMA RESPONSE
# -------------------------------
def get_gemini_response(user_message: str, history: list, db_context: str) -> str:
    llm = ChatOllama(
        model="gemma2:9b",
        temperature=0.2,
    )

    system_prompt = f"""You are SAFE AI, an intelligent assistant for the Software Assets Forecasting Engine (SAFE) dashboard.
You help procurement and IT teams understand SaaS license costs, renewals, forecasts, and at-risk users.

STRICT RULES:
1. ONLY answer based on the data provided in the [DATA CONTEXT] section below.
2. If the data context is empty or does not contain enough information, say: "I don't have enough data to answer that. Please refine your query or check the dashboard."
3. Do NOT hallucinate numbers, vendors, or user details.
4. When presenting license counts, show them as whole integers (no decimal points).
5. Do NOT make assumptions beyond what the data shows.
6. Be concise, structured, and use bullet points or tables where helpful.
7. Always mention which vendor and month(s)/quarter the data refers to.
8. For budget/spend queries, the data contains THREE rows per tier: 'New Acquisitions', 'Renewals', and 'Combined Total'. Always present all three clearly for each tier, then a grand combined total across all tiers.
9. For quarterly data, label it clearly as "Upcoming Quarter (Q? YYYY)".
10. ALWAYS show BOTH licenses AND cost for every license tier — never omit the cost column. Format each tier as: <tier>: <N> licenses, $<cost> (e.g. "Full: 339 licenses, $15,255").
10.5. For questions pertaining to spikes in a month or quarter, if only one month of data is available, 
do NOT ask for historical data. Instead, analyze the current month's data and highlight which license 
tiers contribute most to the total forecasted cost. Present it as a cost breakdown analysis. 
Example: "Based on August 2026 data, the highest cost drivers are Full licenses (124 licenses, $5,580) 
and Editor licenses (133 licenses, $3,990), which together account for 77% of the total $12,220 
forecasted cost."
11. End every forecast or budget response with a Grand Total line showing total licenses and total cost.
12. NEVER ask the user for more data or historical context. Work only with what is in [DATA CONTEXT]. 
If comparison is impossible, reframe the answer as a cost breakdown or cost driver analysis instead.
[DATA CONTEXT]
{db_context if db_context else "No data was retrieved for this query."}
"""

    messages = [SystemMessage(content=system_prompt)]
    for turn in history[-6:]:
        role    = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_message))

    print("\n" + "=" * 60)
    print("📤 CONTEXT SENT TO LLM")
    print("=" * 60)
    print(f"USER MESSAGE: {user_message}")
    print(f"HISTORY TURNS: {len(history[-6:])}")
    print("-" * 60)
    print(db_context if db_context else "No data retrieved")
    print("=" * 60 + "\n")

    response = llm.invoke(messages)
    return response.content


# -------------------------------
# 🚦 MAIN HANDLER  [ENHANCED]
# -------------------------------
pending_state = {}

def handle_query(user_message: str, history: list, session_id: str = "default") -> str:
    """
    Main entry point. Returns bot response string.

    Changes vs original:
      • extract_months now handles quarter keywords → 3 month dates
      • budget intent uses the new query_budget() for total spend
      • quarterly budget / forecast works end-to-end without extra prompting
    """
    msg_lower = user_message.lower()
    if is_case2_sourcing_request(user_message, history):
        return handle_case2_query(user_message, history, session_id)

    intent    = detect_intent(user_message)
    vendor    = extract_vendor(user_message, history)
    months    = extract_months(user_message, history)   # ← quarter-aware

    if intent == "overview":
        return build_context(intent, vendor or "", months, [])

    # --- Step 1: Resolve pending vendor clarification ---
    if session_id in pending_state:
        state = pending_state[session_id]

        if state.get("waiting_for") == "vendor":
            for v in KNOWN_VENDORS:
                if v in msg_lower:
                    vendor = v
                    pending_state[session_id]["vendor"] = vendor
                    pending_state[session_id].pop("waiting_for")

                    if state.get("intent") == "summary" and not months:
                        pending_state[session_id]["waiting_for"] = "month"
                        return f"Got it! For **{vendor}**, which month(s) would you like the summary for?\n- May\n- June\n- Both"
                    else:
                        intent = state.get("intent", intent)
                        months = months or state.get("months", get_next_month())
                        del pending_state[session_id]
                        splits     = extract_splits(user_message)
                        db_context = build_context(intent, vendor, months, splits)
                        if intent == "mail":
                            return "Executing email task..."
                        return get_gemini_response(user_message, history, db_context)

            return f"Sorry, I didn't catch a valid vendor. Please specify one of: {', '.join(KNOWN_VENDORS)}"

        if state.get("waiting_for") == "month":
            vendor = state.get("vendor") or vendor
            if "both" in msg_lower:
                months = ["2026-05-01", "2026-06-01"]
            elif "quarter" in msg_lower or "upcoming" in msg_lower:
                months = get_upcoming_quarter_months()
            elif "may" in msg_lower:
                months = ["2026-05-01"]
            elif "june" in msg_lower:
                months = ["2026-06-01"]
            else:
                return "Please choose: **May**, **June**, **Both**, or **Upcoming Quarter**."

            intent = state.get("intent", "summary")
            del pending_state[session_id]

            if not vendor:
                pending_state[session_id] = {"intent": intent, "months": months, "waiting_for": "vendor"}
                return f"Which vendor would you like the summary for?\nAvailable: {', '.join(KNOWN_VENDORS)}"

            splits     = extract_splits(user_message)
            db_context = build_context(intent, vendor, months, splits)
            if intent == "mail":
                return "Executing email task..."
            return get_gemini_response(user_message, history, db_context)

    # --- Step 2: Fresh query ---

    if not vendor:
        pending_state[session_id] = {"intent": intent, "months": months, "waiting_for": "vendor"}
        return f"Which vendor would you like to look at?\nAvailable: {', '.join(KNOWN_VENDORS)}"

    if intent == "summary":
        if not months:
            pending_state[session_id] = {"intent": "summary", "vendor": vendor, "waiting_for": "month"}
            return (
                f"For **{vendor}**, which month(s) would you like the summary for?\n"
                "- May\n- June\n- Both\n- Upcoming Quarter"
            )
        splits     = extract_splits(user_message)
        db_context = build_context(intent, vendor, months, splits)
        return get_gemini_response(user_message, history, db_context)

    # Per-intent month defaults:
    #   renewal  → May 2026 (contract start month, always from May)
    #   forecast / budget → next calendar month
    #   others   → next calendar month
    if not months:
        if intent == "renewal":
            months = ["2026-05-01"]
        else:
            months = get_next_month()

    splits     = extract_splits(user_message)
    db_context = build_context(intent, vendor, months, splits)
    if intent in ("mail", "overview"):
        return db_context
    return get_gemini_response(user_message, history, db_context)
