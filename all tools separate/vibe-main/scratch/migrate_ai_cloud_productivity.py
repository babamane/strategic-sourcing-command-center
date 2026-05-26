import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

MOCK_DATA = {
    "google": {
        "content": """## Google AI, Cloud, and Productivity Updates

Google's AI strategy focuses on infusing its Gemini family of models across search, advertising, and its Workspace ecosystem, alongside scaling Google Cloud Platform for AI training and inference.

## Cloud Revenue & Market Position
Cloud revenue: $9.5B for Q1 2024, up 28% YoY
Market share: 11% globally, placing Google Cloud behind AWS and Microsoft Azure
Key growth driver: Accelerating enterprise adoption of the Vertex AI development platform

## AI Product Launches
- Gemini 1.5 Pro: Features a groundbreaking 1 million token context window for enterprise processing
- Imagen 3: Next-generation image generation model offering advanced text-to-image quality
- Gemini Live: Conversational audio interface deployed to mobile users in August 2024

## Productivity Updates
- Gemini for Google Workspace: Directly integrated into Gmail, Docs, and Slides for automated content drafting
- Google Sheets Smart Fill: AI-assisted data formatting and structured column generation
- Gemini Side Panel: Unified workspace panel launched to 15 million paid active enterprise users

## Enterprise Features
- Vertex AI Search and Conversation: Zero-retention data privacy environment for enterprise search engines
- Gemini Security Advisor: Automated threat detection and vulnerability remediation in Workspace
- Strategic Alliance: Global enterprise expansion partnership formed with Accenture in early 2024""",
        "sources": [
            {"title": "Alphabet Announces First Quarter 2024 Results", "url": "https://abc.xyz/investor/earnings/"},
            {"title": "Google Cloud Vertex AI Adoption Metrics", "url": "https://cloud.google.com/press"},
            {"title": "Gemini Workspace Enterprise Deployment Guide", "url": "https://workspace.google.com/blog"}
        ]
    },
    "microsoft": {
        "content": """## Microsoft AI, Cloud, and Productivity Updates

Microsoft is scaling enterprise productivity by embedding Copilot throughout Microsoft 365, Windows, and GitHub, backed by its commercial Azure AI infrastructure.

## Cloud Revenue & Market Position
Cloud revenue: $26.7B in Q3 FY24, up 21% YoY
Market share: 25% globally, maintaining a strong second place behind AWS
Key growth driver: Azure AI services customer base growing to over 53,000 active accounts

## AI Product Launches
- Copilot for Microsoft 365: Generative assistant launched to over 10 million enterprise subscribers
- GitHub Copilot Workspace: AI-native developer environment for complete code reviews
- Phi-3: Family of open small language models optimized for local enterprise deployment

## Productivity Updates
- Copilot in Excel: Natural language data modeling and automatic pivot table generation
- Microsoft Teams Intelligent Recap: Automatic meeting notes and action items deployed in June 2024
- Windows 11 Copilot: System-level AI assistant available across 150 million compatible PCs

## Enterprise Features
- Azure OpenAI Service: Compliance certified under HIPAA and SOC 2 guidelines
- Purview Copilot Integration: Automated data governance and compliance discovery
- Strategic Partnership: Deployed unified commercial AI platforms under a multi-billion deal with Coca-Cola""",
        "sources": [
            {"title": "Microsoft Fiscal Year 2024 Third Quarter Earnings", "url": "https://www.microsoft.com/en-us/investor"},
            {"title": "Azure AI Enterprise Growth Metrics", "url": "https://azure.microsoft.com/blog"},
            {"title": "Microsoft 365 Copilot Adoption Index", "url": "https://www.microsoft.com/en-us/worklab"}
        ]
    },
    "adobe": {
        "content": """## Adobe AI, Cloud, and Productivity Updates

Adobe is integrating generative AI into its digital media suite Creative Cloud via its brand-safe Firefly model family to optimize content creation workflows.

## AI Product Launches
- Firefly Image 3: Advanced commercial generative model with high-fidelity control features
- Photoshop Generative Fill: AI-driven image modification adopted by 85% of active designers
- Firefly Vector Model: Industry first vector graphic generation tool released in May 2024

## Productivity Updates
- Acrobat AI Assistant: Automated document summaries and conversational analysis across PDF files
- Adobe Express Generative AI: Mobile content creation engine that surpassed 100 million total downloads
- Creative Cloud Libraries: Automated asset tagging and collaborative creative cloud sharing

## Enterprise Features
- Firefly Enterprise Custom Models: Brand-compliant generative models trained on specific company assets
- Adobe Content Credentials: Cryptographic metadata standard for digital content provenance tracking
- Microsoft Copilot Integration: Content generation connector launched for enterprise productivity apps""",
        "sources": [
            {"title": "Adobe Reports Record Q2 Fiscal 2024 Revenue", "url": "https://www.adobe.com/investor-relations.html"},
            {"title": "Firefly Generative AI Enterprise Adoption Rates", "url": "https://blog.adobe.com"},
            {"title": "Acrobat AI Assistant Deployment metrics", "url": "https://news.adobe.com"}
        ]
    },
    "salesforce": {
        "content": """## Salesforce AI, Cloud, and Productivity Updates

Salesforce's strategy focuses on building autonomous AI agents under the Agentforce ecosystem to manage customer service, sales, and marketing campaigns directly on Customer 360 data.

## AI Product Launches
- Agentforce: Autonomous service agents capable of resolving 90% of basic customer queries
- Einstein Copilot: Conversational CRM assistant launched to all Salesforce Enterprise users
- Prompt Builder: Custom generative prompt development environment for sales representatives

## Productivity Updates
- Slack AI: Automated thread summaries and channel searches deployed globally in early 2024
- Slack Lists: Structured project management tables with integrated automation features
- Einstein 1 Platform: Unified customer data platform that processes 100 billion transactions daily

## Enterprise Features
- Einstein Trust Layer: Zero-retention data privacy architecture preventing AI model data leaks
- Data Cloud Snowflake Integration: Real-time zero-copy data sharing between CRM and data lakes
- Federal Certification: Agentforce approved under FedRAMP high authorization standards""",
        "sources": [
            {"title": "Salesforce Q1 FY25 Earnings Release Results", "url": "https://investor.salesforce.com"},
            {"title": "Agentforce Launch and Enterprise Benchmarks", "url": "https://www.salesforce.com/news"},
            {"title": "Slack AI Adoption and Feature Metrics", "url": "https://slack.com/blog"}
        ]
    },
    "cisco": {
        "content": """## Cisco AI, Cloud, and Productivity Updates

Cisco is driving secure networking and observability by integrating security analytics with Splunk's monitoring platform to secure hybrid cloud operations.

## AI Product Launches
- Cisco AI Assistant for Security: Natural language security policy generator released in mid-2024
- Webex AI Codec: Audio and video compression algorithm for low-bandwidth environments
- ThousandEyes WAN Insights: AI-driven network telemetry engine for wide area networks

## Productivity Updates
- Webex Meeting summaries: Automated transcriptions and task extraction in 30 languages
- Webex Slido Integration: Automated real-time polling and feedback systems
- Cisco Spaces: AI-powered workspace analytics platform that tracks physical office occupancy

## Enterprise Features
- Cisco HyperShield: AI-native security architecture designed to shield data centers from threats
- Splunk Enterprise Integration: Observability pipeline connecting network telemetry to threat intelligence
- NVIDIA Partnership: Jointly engineered enterprise AI infrastructure clusters using custom switches""",
        "sources": [
            {"title": "Cisco Reports Third Quarter Fiscal 2024 Results", "url": "https://investor.cisco.com"},
            {"title": "Cisco HyperShield Launch and Product Architecture", "url": "https://newsroom.cisco.com"},
            {"title": "Webex AI Innovations and Collaboration Guide", "url": "https://blog.webex.com"}
        ]
    },
    "cognizant": {
        "content": """## Cognizant AI, Cloud, and Productivity Updates

Cognizant provides global digital transformation consulting, specializing in training enterprise workforces and migrating legacy architectures to hybrid AI environments.

## AI Product Launches
- Cognizant Flowsource: Generative software development platform launched in January 2024
- Cognizant Neuro AI: Multi-agent orchestration engine for automated business processes
- Innovation Lab: Specialized generative AI center established in London in June 2024

## Productivity Updates
- Employee Upskilling: Enrolled 250,000 associates in advanced generative AI training programs
- Developer Copilots: Implemented AI code completion tools for 75,000 software engineers
- internal Operations: Deployed conversational HR assistants reducing ticket response time by 40%

## Enterprise Features
- Microsoft Alliance: Deployed Microsoft 365 Copilot to 100,000 corporate client accounts
- Google Cloud Partnership: Expanded joint generative AI lab to build healthcare business workflows
- AI Certifications: SOC 2 and ISO 27001 compliance standards achieved for all custom AI platforms""",
        "sources": [
            {"title": "Cognizant First Quarter 2024 Financial Results", "url": "https://investors.cognizant.com"},
            {"title": "Cognizant Flowsource Developer Productivity benchmarks", "url": "https://news.cognizant.com"},
            {"title": "Cognizant and Microsoft Partnership Milestones", "url": "https://news.microsoft.com"}
        ]
    },
    "juniper": {
        "content": """## Juniper AI, Cloud, and Productivity Updates

Juniper specializes in AI-native networking solutions powered by Mist AI, automating wireless and wired enterprise networks to minimize operational latency.

## AI Product Launches
- Juniper Mist AI: Cloud-managed wireless access routing platform with automated troubleshooting
- Marvis Minis: Automated network diagnostic simulations that proactively detect wired outages
- AI-Native Campus Fabric: Cloud-based network routing architecture launched in mid-2024

## Productivity Updates
- Marvis Conversational Interface: AI assistant handling 80% of network helpdesk queries
- Mist Wireless Assurance: Proactive signal tracking reducing on-site technician visits by 60%
- Marvis for Zoom: Real-time network telemetry correlation to diagnose active video call drops

## Enterprise Features
- AI-Native Security Platform: Distributed threat detection protecting multi-site networks
- HPE Merger Integration: Combined HPE Aruba and Juniper networking roadmaps post-acquisition
- Mist Cloud Compliance: FedRAMP Moderate authorization achieved for cloud network management""",
        "sources": [
            {"title": "Juniper Networks Reports Q1 2024 Financial Results", "url": "https://investor.juniper.net"},
            {"title": "Juniper Networks Mist AI and Marvis Updates", "url": "https://newsroom.juniper.net"},
            {"title": "HPE to Acquire Juniper Networks Announcement Details", "url": "https://www.hpe.com/us/en/newsroom"}
        ]
    },
    "wipro": {
        "content": """## Wipro AI, Cloud, and Productivity Updates

Wipro leverages its $1B ai360 ecosystem to embed cognitive tools across business operations, consulting, and systems integration services worldwide.

## AI Product Launches
- Wipro ai360: Unified generative AI framework connecting 220,000 consultants
- Wipro Enterprise AI Gateway: Secure API proxy launched in April 2024 for model governance
- Lab45 generative AI platform: High-performance sandbox for developing custom enterprise agents

## Productivity Updates
- Developer Workbench: Automated code reviews and legacy application migrations using AI
- Virtual HR assistant: Conversational portal servicing employee queries in 10 languages
- Process Automation: Deployed AI document parsers that reduced invoice processing cycles by 50%

## Enterprise Features
- AWS Strategic Partnership: Jointly built specialized industry-focused generative AI solutions
- NVIDIA Collaboration: Developed clinical imaging analytics using custom healthcare APIs
- Compliance Framework: AI systems certified under ISO 42001 artificial intelligence standard""",
        "sources": [
            {"title": "Wipro Announces Fourth Quarter Results for Fiscal Year 2024", "url": "https://www.wipro.com/investors/"},
            {"title": "Wipro ai360 Ecosystem Investment and Milestones", "url": "https://www.wipro.com/newsroom"},
            {"title": "Wipro and AWS Join Forces for Generative AI Development", "url": "https://press.aboutamazon.com"}
        ]
    }
}

def migrate():
    mock_dir = BASE_DIR / "mock_data"
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        json_file = vendor_dir / "highlights_ai_cloud_productivity.json"
        
        data = MOCK_DATA.get(vendor)
        if data:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Successfully migrated highlights_ai_cloud_productivity.json for {vendor.upper()}")

if __name__ == "__main__":
    migrate()
    print("Migration complete!")
