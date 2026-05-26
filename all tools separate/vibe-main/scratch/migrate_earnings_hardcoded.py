import os
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent

COMPANIES = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

# Precooked mock data based on realistic Q1 2024 earnings
MOCK_DATA = {
    "adobe": {
        "content": "## Overview\nAdobe reported strong Q1 2024 results, achieving $5.18B in revenue (up 11% YoY) and an EPS of $4.48, beating estimates of $4.38. The quarter was highlighted by robust enterprise adoption of Firefly AI integration across the Creative Cloud suite.\n\n## Key Takeaways\n- Total revenue reached a record $5.18B, reflecting 11% YoY growth\n- Digital Media segment revenue grew 12% YoY to $3.82B\n- Document Cloud revenue increased 18% YoY to $750M\n- RPO (Remaining Performance Obligations) reached $17.58B, providing strong forward visibility\n\n## Highlights\n- Firefly AI models surpassed 6.5 billion generations globally\n- Acrobat AI Assistant saw rapid enterprise adoption, expanding document intelligence capabilities\n- Achieved record cash flows from operations of $1.17B during the quarter\n\n## Investment Focus Areas\n- **Products**: Acrobat AI Assistant, Premiere Pro generative AI workflows, Adobe Express\n- **AI & Cloud**: Scaling Firefly foundational models and expanding enterprise AI infrastructure\n- **Strategic Priorities**: Monetizing generative AI across enterprise segments and expanding the Document Cloud ecosystem",
        "sources": [{"title": "Adobe Q1 2024 Earnings Release", "url": "https://investors.adobe.com", "date": "March 2024"}]
    },
    "cisco": {
        "content": "## Overview\nCisco's recent quarterly results showcased solid execution in a challenging macro environment, delivering revenue of $12.8B and an EPS of $0.87, slightly above estimates. The quarter's main theme was the successful close of the Splunk acquisition and strong growth in security software.\n\n## Key Takeaways\n- Total revenue stood at $12.8B, down slightly YoY due to supply chain normalization\n- Security segment revenue grew 3% YoY, driven by strong adoption of zero-trust solutions\n- Splunk integration tracking ahead of schedule, expected to add $4B in ARR\n- Software subscription revenue now represents 50% of total revenue\n\n## Highlights\n- Closed the $28 billion acquisition of Splunk, completing the largest deal in Cisco history\n- Hyperscaler orders accelerated, with AI infrastructure investments driving networking demand\n- Security AI Assistant deployment scaled across 1,000+ enterprise customers\n\n## Investment Focus Areas\n- **Products**: Splunk observability platform, Cisco Security Cloud, Silicon One\n- **AI & Cloud**: $1B AI startup investment fund, hyperscaler ethernet switches\n- **Strategic Priorities**: Shifting to recurring software revenue and dominating AI networking infrastructure",
        "sources": [{"title": "Cisco Q3 FY24 Financial Results", "url": "https://investor.cisco.com", "date": "May 2024"}]
    },
    "cognizant": {
        "content": "## Overview\nCognizant reported resilient quarterly results with revenue of $4.76B and an EPS of $1.12. The quarter was characterized by cautious client spending in financial services, offset by strong momentum in healthcare and significant large deal wins centered around AI transformations.\n\n## Key Takeaways\n- Revenue of $4.76B, a slight decrease of 1% YoY in constant currency\n- Healthcare segment grew 2% YoY, acting as the primary growth driver\n- Bookings margin remained strong, with a trailing 12-month book-to-bill ratio of 1.1x\n- NextGen initiatives generated $150M in annualized cost savings\n\n## Highlights\n- Secured 3 large deals valued over $100M each in the quarter\n- Launched Advanced AI Lab in San Francisco to co-innovate with major tech partners\n- Achieved 15% growth in generative AI pipeline across enterprise clients\n\n## Investment Focus Areas\n- **Products**: Bluebolt AI platform, Cognizant Neuro IT operations\n- **AI & Cloud**: $1B investment commitment in generative AI over three years\n- **Strategic Priorities**: Accelerating large deal momentum and optimizing delivery delivery through AI automation",
        "sources": [{"title": "Cognizant Q1 2024 Earnings", "url": "https://investors.cognizant.com", "date": "May 2024"}]
    },
    "google": {
        "content": "## Overview\nAlphabet (Google) delivered exceptional Q1 2024 results, reporting revenue of $80.54B (up 15% YoY) and an EPS of $1.89, easily beating estimates of $1.51. The quarter's main theme was the successful monetization of Gemini AI across Search and Cloud, alongside the announcement of their first-ever dividend.\n\n## Key Takeaways\n- Total revenue reached $80.54B, driven by a 14% YoY increase in Search and 28% YoY growth in Google Cloud\n- Google Cloud achieved $9.57B in revenue with a record operating margin of 9%\n- YouTube ad revenue surged 21% YoY to $8.09B\n- Authorized a new $70B share repurchase program and initiated a $0.20 per share quarterly dividend\n\n## Highlights\n- Capital expenditures increased to $12B, heavily focused on AI compute infrastructure\n- Over 1 million developers are now utilizing Gemini API across Google Cloud platforms\n- AI Overviews in Search began rolling out to US users, showing strong engagement metrics\n\n## Investment Focus Areas\n- **Products**: Gemini Advanced, Google Workspace AI integration, YouTube Shorts\n- **AI & Cloud**: Multi-billion dollar investments in custom TPUs and global data center expansion\n- **Strategic Priorities**: Defending Search dominance through AI integration and accelerating enterprise cloud adoption",
        "sources": [{"title": "Alphabet Q1 2024 Earnings Release", "url": "https://abc.xyz/investor", "date": "April 2024"}]
    },
    "juniper": {
        "content": "## Overview\nJuniper Networks reported quarterly revenue of $1.15B and an EPS of $0.29. The quarter was heavily influenced by the pending acquisition by Hewlett Packard Enterprise (HPE) and saw temporary pauses in enterprise spending, though AI-native networking solutions continued to show robust demand.\n\n## Key Takeaways\n- Total revenue of $1.15B, down 16% YoY due to customer inventory digestion\n- Enterprise revenue declined 8% YoY but remains the largest customer vertical\n- Software and related services revenue accounted for nearly 30% of total revenue\n- ARR (Annualized Recurring Revenue) grew steadily despite hardware headwinds\n\n## Highlights\n- Mist AI platform continued to see double-digit growth in new logo acquisitions\n- Deployed 400G and 800G AI data center solutions for major tier-1 cloud providers\n- Pending $14B acquisition by HPE remains on track to close by late 2024/early 2025\n\n## Investment Focus Areas\n- **Products**: Mist AI, Apstra data center automation, PTX Series routers\n- **AI & Cloud**: Expanding AI-Native Networking Platform capabilities\n- **Strategic Priorities**: Managing the transition to HPE and maintaining enterprise market share",
        "sources": [{"title": "Juniper Networks Q1 2024 Financial Results", "url": "https://investor.juniper.net", "date": "April 2024"}]
    },
    "microsoft": {
        "content": "## Overview\nMicrosoft reported a stellar Q3 FY24 with revenue of $61.9B (up 17% YoY) and an EPS of $2.94, beating estimates of $2.82. The quarter was defined by massive AI-driven acceleration in Azure and the successful broad deployment of Copilot across the enterprise ecosystem.\n\n## Key Takeaways\n- Total revenue of $61.9B, marking 17% YoY growth\n- Intelligent Cloud revenue reached $26.7B (up 21% YoY)\n- Azure revenue grew 31% YoY, with 7 points of growth directly attributed to AI services\n- Productivity and Business Processes revenue grew 12% YoY to $19.6B\n\n## Highlights\n- Capital expenditures soared to $14B to support surging cloud and AI infrastructure demand\n- Over 65% of Fortune 500 companies now use Azure OpenAI Service\n- GitHub Copilot surpassed 1.8 million paid subscribers, a 35% quarter-over-quarter increase\n\n## Investment Focus Areas\n- **Products**: Microsoft 365 Copilot, Azure OpenAI, Dynamics 365 AI tools\n- **AI & Cloud**: Global data center expansion, custom Maia AI accelerators\n- **Strategic Priorities**: Embedding Copilot in every product surface and leading the enterprise AI platform shift",
        "sources": [{"title": "Microsoft Q3 FY24 Earnings", "url": "https://www.microsoft.com/en-us/investor", "date": "April 2024"}]
    },
    "salesforce": {
        "content": "## Overview\nSalesforce reported Q1 FY25 revenue of $9.13B (up 11% YoY) and an EPS of $2.44, slightly missing consensus estimates. The quarter reflected disciplined cost management leading to record margins, alongside early monetization signals from their newly launched Einstein 1 Platform.\n\n## Key Takeaways\n- Revenue reached $9.13B, reflecting 11% YoY growth\n- Achieved a record non-GAAP operating margin of 32.1%\n- Remaining Performance Obligation (RPO) ended at $53.9B, up 15% YoY\n- Data Cloud emerged as the fastest-growing organic product in company history\n\n## Highlights\n- Generated record operating cash flow of $6.25B (up 39% YoY)\n- Einstein Copilot entered general availability, driving significant pipeline interest\n- Paid out the company's first-ever quarterly dividend of $0.40 per share\n\n## Investment Focus Areas\n- **Products**: Data Cloud, Einstein 1 Platform, MuleSoft AI integrations\n- **AI & Cloud**: Enhancing foundational models for CRM-specific workflows\n- **Strategic Priorities**: Driving profitable growth and accelerating Data Cloud adoption as the foundation for AI",
        "sources": [{"title": "Salesforce Q1 FY25 Results", "url": "https://investor.salesforce.com", "date": "May 2024"}]
    },
    "wipro": {
        "content": "## Overview\nWipro reported Q4 FY24 revenue of $2.66B and an EPS of $0.06. The quarter highlighted a stabilization in IT services demand under new leadership, with a strong focus on margin defense and a significant uptick in large transformational AI deals.\n\n## Key Takeaways\n- IT Services revenue of $2.66B, down 4% YoY in constant currency\n- IT Services operating margin expanded by 40 basis points sequentially to 16.4%\n- Total bookings stood at $3.6B, with large deal bookings of $1.2B\n- Voluntary attrition moderated significantly to a 12-month trailing rate of 14.2%\n\n## Highlights\n- New CEO Srini Pallia took leadership, emphasizing execution and agility\n- Trained over 220,000 employees on generative AI fundamentals\n- Secured a landmark $500M+ telecommunications transformation deal\n\n## Investment Focus Areas\n- **Products**: Wipro Enterprise Generative AI (WeGA) framework, FullStride Cloud\n- **AI & Cloud**: $1B committed investment into AI innovation and ecosystem partnerships\n- **Strategic Priorities**: Regaining growth momentum under new leadership and scaling industry-specific AI solutions",
        "sources": [{"title": "Wipro Q4 FY24 Earnings", "url": "https://www.wipro.com/investors/", "date": "April 2024"}]
    }
}

def main():
    for company in COMPANIES:
        mock_path = project_root / "mock_data" / company / "earnings.json"
        
        if mock_path.exists():
            with open(mock_path, "w", encoding="utf-8") as f:
                json.dump(MOCK_DATA[company], f, indent=4)
            print(f"Successfully migrated {company}")
        else:
            print(f"Skipped {company}, directory not found")

if __name__ == "__main__":
    main()
