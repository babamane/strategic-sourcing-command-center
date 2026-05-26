import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

MOCK_DATA = {
    "google": {
        "content": """## Google Pricing Updates

Google's enterprise strategy leverages competitive bundles and API usage pricing, prioritizing volume adoption of Vertex AI over high per-user licenses.

## Key Price Changes
- Google Workspace Business Starter: 20% increase, $6.00 -> $7.20/user/month (effective April 2024)
- Gemini Advanced Tier: $19.99/user/month premium add-on (effective February 2024)
- Vertex AI Gemini 1.5 Flash API: 78% reduction, $0.000125 -> $0.000075/1K input tokens (effective June 2024)

## Business Impact
- Promotes rapid developer onboarding and deployment with extremely low entry-level API costs
- Adds 15% increase in total annualized recurring revenue across baseline Workspace users
- Compresses competitor margins in enterprise large language model inference pricing

## What This Means
- Reevaluate bulk API consumption models to capitalize on recent token cost drops
- Expect a small price push on core baseline workspace renewals in the coming fiscal year
- Focus negotiations on committed use discounts for long-term Vertex AI enterprise workloads""",
        "sources": [
            {"title": "Google Workspace Pricing Updates Announcement", "url": "https://workspace.google.com/blog", "date": "2024-02-15"},
            {"title": "Gemini Advanced Tier Pricing and Release", "url": "https://blog.google/technology/ai/", "date": "2024-02-08"},
            {"title": "Google Cloud Vertex AI API Cost Reductions", "url": "https://cloud.google.com/blog", "date": "2024-06-14"}
        ]
    },
    "microsoft": {
        "content": """## Microsoft Pricing Updates

Microsoft is monetizing its early lead in generative AI by introducing dedicated, high-margin premium add-on licenses across commercial office suites.

## Key Price Changes
- Copilot for Microsoft 365: $30.00/user/month flat add-on with no minimum seats (effective January 2024)
- Power BI Premium per user: 10% increase, $20.00 -> $22.00/user/month (effective July 2024)
- Azure OpenAI GPT-4o: 50% price decrease for input tokens, $0.01 -> $0.005/1K tokens (effective May 2024)

## Business Impact
- Adds up to 60% additional cost overhead for early enterprise adopters of generative office tools
- Lowers baseline platform costs for developers testing customized GPT architectures
- Expands commercial average revenue per user to record levels across the sector

## What This Means
- Budget strictly for Copilot seat allocations based on role productivity audits
- Leverage volume agreements during Azure subscription negotiations to offset core pricing increases
- Benchmark performance metrics of Azure custom models to justify high seat costs""",
        "sources": [
            {"title": "Microsoft Commercial Copilot Pricing Details", "url": "https://www.microsoft.com/en-us/investor", "date": "2024-01-15"},
            {"title": "Power BI License Price Change Announcement", "url": "https://powerbi.microsoft.com/blog", "date": "2024-05-10"},
            {"title": "Azure OpenAI GPT-4o Token Cost Updates", "url": "https://azure.microsoft.com/blog", "date": "2024-05-13"}
        ]
    },
    "adobe": {
        "content": """## Adobe Pricing Updates

Adobe has introduced generative credit consumption metrics alongside its subscription plans to limit heavy computing overhead from AI design generations.

## Key Price Changes
- Creative Cloud All Apps: 9% increase, $82.49 -> $89.99/user/month (effective November 2023)
- Adobe Firefly Generative Credits: $4.99/100 credits add-on package (effective January 2024)
- Photoshop Single App: 10% increase, $20.99 -> $22.99/user/month (effective November 2023)

## Business Impact
- Shifts enterprise budgets from flat creative fees to variable usage metrics
- Increases annual creative suite licensing fees by approximately 8.5% across typical operations
- Drives mid-market customer searches for alternative non-AI editing applications

## What This Means
- Track active enterprise credit consumption to prevent unexpected overage fees
- Consolidate active Creative Cloud licenses down to essential users prior to contract renewal
- Renegotiate bulk contract renewals by packaging credit bundles with core software licenses""",
        "sources": [
            {"title": "Adobe Creative Cloud Pricing Adjustments 2023", "url": "https://www.adobe.com/investor-relations.html", "date": "2023-09-14"},
            {"title": "Firefly Generative Credits Subscription Details", "url": "https://blog.adobe.com", "date": "2023-11-01"},
            {"title": "Photoshop Single App Price Modification Guide", "url": "https://news.adobe.com", "date": "2023-09-20"}
        ]
    },
    "salesforce": {
        "content": """## Salesforce Pricing Updates

Salesforce has updated standard list prices across major cloud suites to offset the high developer research and development costs of autonomous AI agents.

## Key Price Changes
- Salesforce Sales Cloud Enterprise: 9% increase, $150.00 -> $165.00/user/month (effective August 2023)
- Service Cloud Unlimited: 9% increase, $300.00 -> $325.00/user/month (effective August 2023)
- Einstein Copilot Add-On: $50.00/user/month flat premium licensing (effective March 2024)

## Business Impact
- Represents the first major base license list price increase in seven years across core suites
- Raises enterprise customer total cost of ownership across Customer 360 systems
- Sets high entry margins for next-generation generative workflow pilots

## What This Means
- Review low-usage CRM seats for cancellation before next renewal cycle
- Seek long-term multi-year price locks on base product offerings during contract discussions
- Demand measurable ROI verification before rolling out the premium Einstein add-ons to workforce""",
        "sources": [
            {"title": "Salesforce Pricing Increases Across Core Clouds", "url": "https://investor.salesforce.com", "date": "2023-07-11"},
            {"title": "Einstein Copilot Enterprise Licensing Launch", "url": "https://www.salesforce.com/news", "date": "2024-03-05"}
        ]
    },
    "cisco": {
        "content": """## Cisco Pricing Updates

Cisco is consolidating security and networking packages post-Splunk to offer highly-integrated unified enterprise licensing agreements.

## Key Price Changes
- Cisco Duo Advantage: 8% increase, $6.00 -> $6.50/user/month (effective March 2024)
- Splunk Cloud Developer Tier: 12% price reduction on standard data ingestion rates (effective May 2024)
- Webex Suite Enterprise Package: $11.95/user/month unified bundle pricing (effective February 2024)

## Business Impact
- Incentivizes consolidated platform buying over standalone point solutions across security stacks
- Promotes rapid security scaling by simplifying user-based billing structures
- Lowers data storage cost barriers for enterprise observability pipelines

## What This Means
- Leverage unified ELA agreements to bundle legacy Cisco products with newly acquired Splunk features
- Transition standalone meeting software contracts to Cisco's cheaper unified suite where applicable
- Baseline ELA commitments against historical telemetry usage to avoid paying for unused headroom""",
        "sources": [
            {"title": "Cisco Duo Multi-Factor Authentication Pricing Updates", "url": "https://investor.cisco.com", "date": "2024-01-20"},
            {"title": "Splunk Ingestion Pricing Optimization Details", "url": "https://newsroom.cisco.com", "date": "2024-04-18"},
            {"title": "Webex Unified Suite Launch And Bundling Rates", "url": "https://blog.webex.com", "date": "2024-02-05"}
        ]
    },
    "cognizant": {
        "content": """## Cognizant Pricing Updates

Cognizant utilizes value-based pricing and global delivery center leverage to bundle consulting services with generative AI platform pilot projects.

## Key Price Changes
- Neuro AI Pilot Engagement: 15% reduction on initial proof-of-concept phase costs (effective Q1 2024)
- Cloud Migration Delivery Rates: 5% increase for premium on-shore consulting (effective April 2024)
- Flowsource Integration Package: $12,500/flat setup fee for custom developer portals (effective January 2024)

## Business Impact
- Encourages enterprise customers to initiate experimental digital modernization pilots at low cost
- Increases service maintenance costs for legacy architectures reliant on physical on-site engineers
- Standardizes entry costs for proprietary software modernization tools

## What This Means
- Push for fixed-price engagement contracts to prevent budget inflation on services
- Leverage early setup fee waivers during multi-year service contract discussions
- Focus on off-shore consulting resources to offset premium on-shore rate increases""",
        "sources": [
            {"title": "Cognizant Q1 2024 Earnings and Pricing Index", "url": "https://investors.cognizant.com", "date": "2024-05-02"},
            {"title": "Cognizant Flowsource Integration Setup Metrics", "url": "https://news.cognizant.com", "date": "2024-01-18"}
        ]
    },
    "juniper": {
        "content": """## Juniper Pricing Updates

Juniper continues to tie pricing value to its Mist AI networking software to reduce overall operational troubleshooting expenditures.

## Key Price Changes
- Mist Wireless LAN Subscription: 6% increase, $120.00 -> $127.00/device/year (effective February 2024)
- Marvis Virtual Network Assistant: $49.00/access point/year subscription rate (effective January 2024)
- Mist Wired Assurance Package: 5% price reduction on bulk access switch bundles (effective March 2024)

## Business Impact
- Increases software licensing costs for distributed smart physical office spaces
- Demonstrates strong operational savings by reducing network helpdesk tickets by up to 45%
- Lowers initial hardware procurement expenses for multi-site campus expansions

## What This Means
- Quantify Mist AI helpdesk cost reductions to justify subscription cost increases during audits
- Negotiate multi-year Mist subscriptions together with new physical switch rollouts
- Phase out legacy standalone routers in favor of unified AI-native campus bundles""",
        "sources": [
            {"title": "Juniper Networks Mist Subscription Rate Adjustment", "url": "https://investor.juniper.net", "date": "2024-01-10"},
            {"title": "Mist AI and Wired Switch Bundle Packages Release", "url": "https://newsroom.juniper.net", "date": "2024-02-28"}
        ]
    },
    "wipro": {
        "content": """## Wipro Pricing Updates

Wipro utilizes value-driven consulting agreements and outcome-based pricing frameworks to scale its generative AI integration services.

## Key Price Changes
- ai360 Discovery Workshop: $7,500/flat starter package (effective January 2024)
- Managed Services Global Delivery: 4% average rate increase across mid-level engineering (effective March 2024)
- Enterprise AI Gateway Customizer: $15,000/flat setup fee for custom portals (effective April 2024)

## Business Impact
- Lowers upfront risk for enterprise clients initiating digital workspace migrations
- Moderately increases maintenance operational costs for multi-vendor consulting agreements
- Stabilizes cost boundaries for proprietary software governance tools

## What This Means
- Structure consulting agreements around clear delivery milestones instead of flat hourly rates
- Negotiate rate caps on junior and mid-level engineering hours during renewal negotiations
- Bundle Customizer portal development with core cloud transformation contracts to minimize overhead""",
        "sources": [
            {"title": "Wipro FY24 Earnings Financial Release Summary", "url": "https://www.wipro.com/investors/", "date": "2024-04-19"},
            {"title": "Wipro Enterprise AI Gateway and Setup Packages", "url": "https://www.wipro.com/newsroom", "date": "2024-04-10"}
        ]
    }
}

def migrate():
    mock_dir = BASE_DIR / "mock_data"
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        json_file = vendor_dir / "highlights_pricing_insights.json"
        
        data = MOCK_DATA.get(vendor)
        if data:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Successfully migrated highlights_pricing_insights.json for {vendor.upper()}")

if __name__ == "__main__":
    migrate()
    print("Migration complete!")
