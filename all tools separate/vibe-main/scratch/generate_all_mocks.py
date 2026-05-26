import os
import json

companies = [
    {"id": "microsoft", "name": "Microsoft", "symbol": "MSFT"},
    {"id": "google", "name": "Google", "symbol": "GOOGL"},
    {"id": "salesforce", "name": "Salesforce", "symbol": "CRM"},
    {"id": "adobe", "name": "Adobe", "symbol": "ADBE"},
    {"id": "cisco", "name": "Cisco", "symbol": "CSCO"},
    {"id": "juniper", "name": "Juniper", "symbol": "JNPR"},
    {"id": "cognizant", "name": "Cognizant", "symbol": "CTSH"},
    {"id": "wipro", "name": "Wipro", "symbol": "WIT"}
]

def generate_mock_data():
    base_dir = "mock_data"
    os.makedirs(base_dir, exist_ok=True)
    
    for company in companies:
        comp_dir = os.path.join(base_dir, company["id"])
        os.makedirs(comp_dir, exist_ok=True)
        
        # 1. Earnings
        earnings = {
            "announce_date": "2025-10-15",
            "eps_estimated": "$2.50",
            "eps_actual": "$2.75",
            "eps_surprise_percent": "Beat by 10%",
            "revenue_actual": "$45.2B",
            "revenue_surprise": "Beat by $500M",
            "summary": f"{company['name']} reported strong quarterly results with growth across all major segments. The management highlighted the successful integration of AI features into their core product offerings, leading to increased customer retention and upsell opportunities."
        }
        with open(os.path.join(comp_dir, "earnings.json"), "w") as f:
            json.dump(earnings, f, indent=2)
            
        # 2. Highlights Tabs
        tabs = [
            ("vendor_topics", "Vendor Discussion Topics"),
            ("pricing_insights", "Pricing Insights"),
            ("products_features", "Products and Features"),
            ("ai_cloud_productivity", "AI, Cloud and Productivity")
        ]
        
        for tab_id, label in tabs:
            data = {
                "content": f"### {label} - {company['name']}\n\n* **Key Update 1**: Detailed analysis of the latest performance metrics and market position.\n* **Strategic Shift**: New initiatives focused on enhancing efficiency and driving innovation.\n* **Growth Area**: Expansion into emerging markets and new customer segments.\n* **Future Outlook**: Positive guidance for the upcoming fiscal year based on current momentum.",
                "sources": []
            }
            with open(os.path.join(comp_dir, f"highlights_{tab_id}.json"), "w") as f:
                json.dump(data, f, indent=2)
                
        # 3. QBR and Briefing
        qbr_content = f"""# Quarterly Business Review - {company['name']}

## Business Performance Overview
- **Steady Growth**: {company['name']} continues to show resilience in a competitive market.
- **Operational Excellence**: Focus on margin expansion through automation and cost management.

## Key Financial Highlights
- **Revenue**: Solid performance across core business units.
- **Profitability**: Net income exceeded analyst estimates.

## Strategic Outlook
- **Innovation Pipeline**: Strong roadmap for AI-driven product enhancements.
- **Market Expansion**: Investing in high-growth opportunities globally.
"""
        with open(os.path.join(comp_dir, "qbr.md"), "w") as f:
            f.write(qbr_content)
            
        briefing_content = f"""# Briefing Document - {company['name']}

**Purpose of This Brief**
Strategic preparation for upcoming executive discussions and partnership reviews with {company['name']}.

**Current State**
{company['name']} is focused on consolidating its market position while pivoting towards AI-centric solutions.

**Priority Discussion Topics**
- Roadmap alignment and co-innovation opportunities.
- Pricing structure and multi-year contract stability.
- Support levels and operational excellence.
"""
        with open(os.path.join(comp_dir, "briefing.md"), "w") as f:
            f.write(briefing_content)

    print("Mock data generation complete for all vendors.")

if __name__ == "__main__":
    generate_mock_data()
