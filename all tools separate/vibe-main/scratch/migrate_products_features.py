import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

MOCK_DATA = {
    "google": {
        "content": """## Google Product and Feature Updates (Last 6-12 Months)

Google's product development is centered around scaling multimodality through its Gemini models, integrating AI assistants cross-platform, and optimizing machine learning infrastructure.

## New Product Launches
Gemini 1.5 Pro and Gemini 1.5 Flash were officially launched in mid-2024 to enhance long-context developer and enterprise operations.
- Gemini 1.5 Pro: Supports up to 2 million token input processing with multimodality
- Gemini 1.5 Flash: Offers high-speed, cost-efficient inference for high-frequency workflows
- Imagen 3: Professional text-to-image engine with advanced brand-safe controls

## Major Feature Updates
Google Workspace received significant upgrades to embed conversational AI into daily operations.
- Gemini Side Panel: Integrated directly inside Google Docs and Gmail in June 2024
- Google Sheets Smart Fill: Automated data preparation pipelines launched in April 2024
- Vertex AI Search: Grounding upgrades allowing zero-copy connections to internal data

## Platform Enhancements
Introduced unified pricing for enterprise API tokens alongside commitment-based Vertex AI developer subscription discounts and multi-region data residency controls.

## Product Deprecations
- Google Universal Analytics end-of-support: July 2024
- Legacy Google Play Movies retiring: January 2024

## Regulatory Updates
Addressed compliance requirements in accordance with the EU AI Act guidelines across all cloud deployments. No new regulatory concerns flagged this quarter.""",
        "sources": [
            {"title": "Google I/O 2024 Developer Announcements", "url": "https://blog.google/technology/developers/", "date": "2024-05-14"},
            {"title": "Google Workspace Gemini Panel Release", "url": "https://workspace.google.com/blog", "date": "2024-06-25"},
            {"title": "Google Cloud Vertex AI Platform Pricing", "url": "https://cloud.google.com/blog", "date": "2024-06-14"},
            {"title": "EU AI Act Compliance and Google Cloud Roadmap", "url": "https://cloud.google.com/security/compliance", "date": "2024-08-01"}
        ]
    },
    "microsoft": {
        "content": """## Microsoft Product and Feature Updates (Last 6-12 Months)

Microsoft focuses on expanding its Copilot AI portfolio across operating systems and developer suites, while optimizing commercial hybrid cloud pipelines.

## New Product Launches
Microsoft launched customized enterprise agent developer portals and local small language models in early 2024.
- Copilot Studio: High-control platform enabling custom agent creation launched in January 2024
- Phi-3: Small footprint local language models optimized for low-compute mobile devices
- GitHub Copilot Workspace: Fully conversational developer workspace released in May 2024

## Major Feature Updates
Expanded automated insights and system assistance capabilities across commercial baseline tools.
- Teams Intelligent Recap: Natural language meeting notes generation deployed in June 2024
- Excel Copilot: Python integration allowing complex data visualization using plain text
- Azure OpenAI GPT-4o: Deployed GPT-4o with double the inference speed in May 2024

## Platform Enhancements
Transitioned core Copilot pricing models to flat enterprise subscriptions with no seat minimums, alongside advanced security logging inside Purview.

## Product Deprecations
- Windows 10 Home and Pro end-of-support planning: October 2025
- Azure API Management developer portal classic version retiring: March 2024

## Regulatory Updates
Maintained compliance with transatlantic data privacy standards. No new regulatory concerns flagged.""",
        "sources": [
            {"title": "Microsoft Copilot Studio Launch Details", "url": "https://www.microsoft.com/en-us/investor", "date": "2024-01-15"},
            {"title": "Phi-3 Small Language Models Release Notes", "url": "https://azure.microsoft.com/blog", "date": "2024-04-23"},
            {"title": "Azure OpenAI GPT-4o Integration Roadmap", "url": "https://azure.microsoft.com/blog", "date": "2024-05-13"},
            {"title": "Microsoft Product Lifecycle and Sunsets Guide", "url": "https://support.microsoft.com/lifecycle", "date": "2024-03-01"}
        ]
    },
    "adobe": {
        "content": """## Adobe Product and Feature Updates (Last 6-12 Months)

Adobe's strategy prioritizes deploying safe generative models within creative software tools to optimize production times while guaranteeing digital asset safety.

## New Product Launches
Adobe launched professional generative credit models and specialized text-to-vector engines in late 2023.
- Firefly Vector Model: Industry first graphic design vector generator released in October 2023
- Firefly Design Model: Custom templates engine launched in early 2024
- Firefly Audio Model: Experimental sound effects editing environment announced in mid-2024

## Major Feature Updates
Embedded generative capabilities into professional photo and layout software suites.
- Photoshop Generative Fill: Deployed with three times faster processing speed in May 2024
- Acrobat AI Assistant: Automated document summarization deployed to all users in April 2024
- Illustrator Text to Vector: Seamless geometric design pipelines launched in November 2023

## Platform Enhancements
Implemented commercial credit billing systems across all plans alongside standard Content Credentials metadata for provenance tracking.

## Product Deprecations
- Adobe XD standalone sales discontinued: June 2023
- Legacy Creative Cloud Synced files end-of-support: February 2024

## Regulatory Updates
No new regulatory concerns. Adobe Firefly models are commercially safe and fully compliant with international IP standards.""",
        "sources": [
            {"title": "Adobe Max 2023 Product Keynote", "url": "https://www.adobe.com/investor-relations.html", "date": "2023-10-10"},
            {"title": "Adobe Acrobat AI Assistant Commercial Launch", "url": "https://news.adobe.com", "date": "2024-04-15"},
            {"title": "Creative Cloud Synced Files Deprecation Notice", "url": "https://helpx.adobe.com", "date": "2024-01-08"},
            {"title": "Content Authenticity Initiative Provenance Tracking", "url": "https://contentauthenticity.org", "date": "2024-02-14"}
        ]
    },
    "salesforce": {
        "content": """## Salesforce Product and Feature Updates (Last 6-12 Months)

Salesforce's product strategy emphasizes building autonomous, low-code AI agents that execute complex customer service workflows directly on active enterprise customer files.

## New Product Launches
Salesforce launched autonomous service agent systems and custom prompt builders in early 2024.
- Agentforce: Low-code autonomous agents platform officially launched in March 2024
- Einstein Copilot: Natural language CRM assistant made generally available in February 2024
- Prompt Builder: Custom prompt engineering workspace launched in February 2024

## Major Feature Updates
Optimized team collaboration and customer data pipelines within the Customer 360 platform.
- Slack AI summaries: Deployed automated thread and channel indexers in March 2024
- Data Cloud Zero Copy: Streamlined real-time connections to Snowflake and Databricks in April 2024
- Service Cloud Einstein: Proactive customer care recommendation engine launched in January 2024

## Platform Enhancements
Introduced flat-rate per-user licenses for premium Einstein features and established the Einstein Trust Layer for prompt privacy governance.

## Product Deprecations
- Legacy Workflow Rules automatic migrations starting: March 2024
- Salesforce Audience Studio retiring: June 2024

## Regulatory Updates
Achieved FedRAMP High Authorization standards for core generative CRM models. No new regulatory concerns.""",
        "sources": [
            {"title": "Salesforce Agentforce Platform Release Details", "url": "https://www.salesforce.com/news", "date": "2024-03-05"},
            {"title": "Einstein Copilot CRM GA Announcement", "url": "https://investor.salesforce.com", "date": "2024-02-27"},
            {"title": "Slack AI Global Integration Rollout", "url": "https://slack.com/blog", "date": "2024-03-12"},
            {"title": "Salesforce Trust and Security Compliance Portal", "url": "https://trust.salesforce.com", "date": "2024-04-10"}
        ]
    },
    "cisco": {
        "content": """## Cisco Product and Feature Updates (Last 6-12 Months)

Cisco is focusing on integrating security operations post-Splunk and deploying AI assistants to simplify corporate network management.

## New Product Launches
Cisco launched custom threat security platforms and intelligent low-bandwidth codecs in early 2024.
- Cisco HyperShield: AI-native security shielding for data centers launched in April 2024
- Cisco AI Assistant for Security: Plain text networking security generator released in Q1 2024
- Webex AI Codec: Next-generation compression codec for ultra-low bandwidth calls

## Major Feature Updates
Improved observability pipelines and simplified video conference coordination tools.
- Webex Meeting Recaps: Deployed automated multi-language meeting summarization in February 2024
- Splunk Cloud Observability: Unified data ingestion linking network telemetry to security logs
- ThousandEyes WAN Insights: Proactive traffic routing recommendation engine released in March 2024

## Platform Enhancements
Unified Cisco and Splunk commercial packages under consolidated enterprise licensing agreements.

## Product Deprecations
- Cisco Prime Infrastructure end-of-sale: June 2024
- Legacy Webex Meetings desktop client version 42 end-of-support: March 2024

## Regulatory Updates
No new regulatory concerns. Security systems fully conform to global NIS2 digital security requirements.""",
        "sources": [
            {"title": "Cisco HyperShield Launch Event", "url": "https://newsroom.cisco.com", "date": "2024-04-18"},
            {"title": "Cisco Duo and Webex Product Enhancements 2024", "url": "https://investor.cisco.com", "date": "2024-02-05"},
            {"title": "Webex AI Codec and Video Platform Release Guide", "url": "https://blog.webex.com", "date": "2024-01-30"},
            {"title": "Cisco NIS2 Compliance and Security Guidance", "url": "https://trustportal.cisco.com", "date": "2024-05-12"}
        ]
    },
    "cognizant": {
        "content": """## Cognizant Product and Feature Updates (Last 6-12 Months)

Cognizant focuses on developing proprietary software automation platforms and building custom digital transformation sandboxes for clients.

## New Product Launches
Cognizant launched software development portals and business orchestration platforms in early 2024.
- Cognizant Flowsource: Automated generative software development portal released in January 2024
- Cognizant Neuro AI: Multi-agent automation and decision orchestration framework launched in early 2024
- Custom Health Lab: Specialized generative AI lab established in June 2024

## Major Feature Updates
Optimized consulting delivery methods and expanded corporate training initiatives.
- Flowsource Code Reviewer: Automated pull request reviews deployed in April 2024
- Neuro AI Medical Assistant: Specialized healthcare analysis module launched in March 2024
- Associate Upskilling: Generative training program extended to 250,000 global staff

## Platform Enhancements
Standardized Neuro AI platform pricing structures and achieved SOC 2 and ISO 42001 certifications across all proprietary software portals.

## Product Deprecations
- Legacy onshore manual coding frameworks retired: December 2023
- Legacy client support portals end-of-support: Q1 2024

## Regulatory Updates
Maintained full compliance with global healthcare and financial data residency guidelines. No new concerns.""",
        "sources": [
            {"title": "Cognizant Flowsource Launch and Benchmarks", "url": "https://news.cognizant.com", "date": "2024-01-18"},
            {"title": "Cognizant Neuro AI Platform Release Notes", "url": "https://news.cognizant.com", "date": "2024-02-28"},
            {"title": "Cognizant Q1 2024 Financial and Operations Review", "url": "https://investors.cognizant.com", "date": "2024-05-02"}
        ]
    },
    "juniper": {
        "content": """## Juniper Product and Feature Updates (Last 6-12 Months)

Juniper's product development focuses on scaling its Mist AI networking engine to automate network maintenance and eliminate physical downtime.

## New Product Launches
Juniper launched automated network diagnostic simulators and campus architectures in early 2024.
- Marvis Minis: Automated digital twin network troubleshooting simulator released in Q1 2024
- AI-Native Campus Fabric: Cloud-based campus routing platform released in mid-2024
- Mist Wireless Access Point AP45: Next-generation Wi-Fi 6E intelligent access point

## Major Feature Updates
Improved troubleshooting automation and optimized video diagnostic systems.
- Marvis Conversational Assistant: Plain text network health queries deployed in January 2024
- Marvis for Zoom: Telemetry data correlation to track meeting call drops released in March 2024
- Mist Wired Assurance: Automated switch diagnostic updates deployed in March 2024

## Platform Enhancements
Achieved FedRAMP Moderate cloud authorization and bundled hardware switch purchases with Mist licensing subscriptions.

## Product Deprecations
- Juniper SRX Series branch firewalls end-of-sale planning: June 2024
- Legacy Mist Classic dashboard interface retiring: December 2023

## Regulatory Updates
No new regulatory concerns. All cloud network management portals conform to moderate security authorization standards.""",
        "sources": [
            {"title": "Juniper Networks Mist AI and Marvis Updates", "url": "https://newsroom.juniper.net", "date": "2024-01-10"},
            {"title": "Juniper Networks Marvis Minis Launch Details", "url": "https://newsroom.juniper.net", "date": "2024-02-20"},
            {"title": "HPE-Juniper Product Alignment and Integration News", "url": "https://www.hpe.com/us/en/newsroom", "date": "2024-03-15"}
        ]
    },
    "wipro": {
        "content": """## Wipro Product and Feature Updates (Last 6-12 Months)

Wipro prioritizes developing specialized generative sandboxes and deploying secure API gateways under its unified ai360 ecosystem.

## New Product Launches
Wipro launched secure API gateways and customized analytical sandboxes in early 2024.
- Enterprise AI Gateway: Secure model routing proxy launched in April 2024
- Lab45 AI Sandbox: High-performance generative workspace released in Q1 2024
- ai360 Framework: Unified digital consulting blueprint launched in late 2023

## Major Feature Updates
Expanded automated testing frameworks and updated legacy code modernization workbench suites.
- Developer Workbench: Generative code modernization tools released in January 2024
- Wipro SmartTest AI: Automated test execution suite deployed in March 2024
- Wipro HR Assistant: Conversational personnel assistant deployed to all corporate staff

## Platform Enhancements
Achieved ISO 42001 certification for artificial intelligence systems and expanded collaborative vertical labs with Amazon Web Services.

## Product Deprecations
- Legacy application testing support systems retired: March 2024
- Legacy local database diagnostic interfaces retiring: June 2024

## Regulatory Updates
No new regulatory concerns. Wipro maintains full compliance with global data localization and security standards.""",
        "sources": [
            {"title": "Wipro ai360 Ecosystem Investment and Launch Details", "url": "https://www.wipro.com/newsroom", "date": "2023-11-08"},
            {"title": "Wipro Enterprise AI Gateway Security Release", "url": "https://www.wipro.com/newsroom", "date": "2024-04-10"},
            {"title": "Wipro Q4 FY24 Financial Earnings Report", "url": "https://www.wipro.com/investors/", "date": "2024-04-19"}
        ]
    }
}

def migrate():
    mock_dir = BASE_DIR / "mock_data"
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        json_file = vendor_dir / "highlights_products_features.json"
        
        data = MOCK_DATA.get(vendor)
        if data:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Successfully migrated highlights_products_features.json for {vendor.upper()}")

if __name__ == "__main__":
    migrate()
    print("Migration complete!")
