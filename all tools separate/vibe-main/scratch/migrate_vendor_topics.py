import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

MOCK_DATA = {
    "google": {
        "pricing_strategy": {
            "summary": "Google recently implemented a 20% price increase on baseline Workspace seats, while lowering high-volume Vertex AI API inputs by 78% to capture large-scale enterprise developer workloads.",
            "discussion_point": "Negotiate long-term price locks on core Workspace licenses by leveraging our planned commitments to Vertex AI API consumption."
        },
        "ai_cloud_integration": {
            "summary": "Gemini 1.5 Pro features a groundbreaking 1 million token context window, alongside Gemini side panel tools now deployed to 15 million active Workspace users.",
            "discussion_point": "Assess integration pathways for large-context enterprise search applications using Vertex AI development platforms."
        },
        "product_roadmap": {
            "summary": "Google is prioritizing conversational audio tools with Gemini Live and embedding natural language smart automation systems throughout Sheets and Docs.",
            "discussion_point": "Seek early access roadmap timelines for automated spreadsheet agents to coordinate internal productivity planning."
        },
        "security_compliance": {
            "context": "Deploying generative workloads on Vertex AI requires strict zero-data-retention guarantees to maintain proprietary data boundaries.",
            "discussion_point": "Confirm zero-retention policies and regulatory compliance models for customized corporate data fine-tuning."
        },
        "partnership_opportunities": {
            "context": "Google has partnered globally with Accenture to deploy enterprise-grade vertical AI tools to specialized industries.",
            "discussion_point": "Explore a tri-party alliance with Google and Accenture to co-develop custom client service workflows."
        }
    },
    "microsoft": {
        "pricing_strategy": {
            "summary": "Microsoft is driving high margins with a flat $30 per-user add-on for M365 Copilot, while dropping Azure OpenAI API input token fees by 50% to maintain developer dominance.",
            "discussion_point": "Audit active Copilot seat adoption metrics before next renewal to align high licensing costs with verified productivity returns."
        },
        "ai_cloud_integration": {
            "summary": "Commercial Azure AI services grew to over 53,000 active accounts, supported by the local deployment capabilities of the small-footprint Phi-3 models.",
            "discussion_point": "Determine feasibility of deploying low-cost Phi-3 small language models locally on corporate hardware to reduce cloud inference fees."
        },
        "product_roadmap": {
            "summary": "Expanding developer collaboration frameworks via GitHub Copilot Workspace, alongside deep system-level assistant integrations in Windows 11.",
            "discussion_point": "Obtain security roadmaps for system-level Copilot integrations to ensure client data protection across enterprise endpoints."
        },
        "security_compliance": {
            "context": "Enterprise usage of Azure OpenAI requires verification of HIPAA and SOC 2 data protection standards across cloud platforms.",
            "discussion_point": "Verify data governance policies regarding prompt logging within Azure OpenAI private enterprise subscriptions."
        },
        "partnership_opportunities": {
            "context": "Microsoft is establishing multi-billion corporate AI partnerships to develop customized commercial operations frameworks.",
            "discussion_point": "Propose a collaborative innovation pilot utilizing Azure OpenAI to build proprietary industry analytical models."
        }
    },
    "adobe": {
        "pricing_strategy": {
            "summary": "Adobe raised Creative Cloud All Apps prices by 9% and introduced a variable credit model ($4.99 per 100 credits) to monetize generative compute workloads.",
            "discussion_point": "Request bundled credits packages with core licensing renewals to prevent unpredictable monthly overage fees."
        },
        "ai_cloud_integration": {
            "summary": "Firefly Image 3 model has been embedded into Photoshop Generative Fill, seeing adoption across 85% of professional creative workflows.",
            "discussion_point": "Evaluate the cost savings of utilizing Firefly-powered workflows vs traditional outsourced graphic design agencies."
        },
        "product_roadmap": {
            "summary": "Prioritizing document intelligence via Acrobat AI Assistant, alongside real-time design automation on Adobe Express mobile applications.",
            "discussion_point": "Request enterprise roadmap previews for Acrobat AI Assistant to evaluate automated legal and procurement document processing."
        },
        "security_compliance": {
            "context": "Enterprise brand compliance requires Adobe's cryptographic Content Credentials to verify asset provenance and digital rights.",
            "discussion_point": "Verify intellectual property indemnification terms for assets generated using Firefly Enterprise custom models."
        },
        "partnership_opportunities": {
            "context": "Adobe is integrating asset generation APIs directly with Microsoft Copilot to streamline collaborative office workflows.",
            "discussion_point": "Evaluate linking our Adobe Creative Cloud assets directly into Microsoft M365 Copilot systems for immediate presentation building."
        }
    },
    "salesforce": {
        "pricing_strategy": {
            "summary": "Salesforce implemented a 9% list price increase across Sales and Service Clouds, introducing Einstein Copilot CRM add-ons at a premium $50 per user rate.",
            "discussion_point": "Renegotiate core Customer 360 seat renewals to demand discount offsets before piloting premium Einstein Copilot features."
        },
        "ai_cloud_integration": {
            "summary": "Salesforce is pivoting to Agentforce, offering autonomous service agents designed to execute complex customer care tasks directly on unified Data Cloud files.",
            "discussion_point": "Review deployment frameworks for Agentforce pilots to automate first-line client support operations."
        },
        "product_roadmap": {
            "summary": "Integrating Slack AI thread summaries and channel indexing closely with real-time Data Cloud feeds for immediate cross-department coordination.",
            "discussion_point": "Request Slack AI product roadmaps to evaluate enterprise data sharing rules and search permission models."
        },
        "security_compliance": {
            "context": "Generative CRM integration requires Salesforce's Einstein Trust Layer to prevent client PII data leaks to external public models.",
            "discussion_point": "Audit Einstein Trust Layer zero-retention policies before connecting live customer data to generative engines."
        },
        "partnership_opportunities": {
            "context": "Salesforce is expanding zero-copy real-time data sharing agreements with major analytics platforms like Snowflake.",
            "discussion_point": "Evaluate implementing zero-copy data bridges between Salesforce CRM and Snowflake data warehouses to streamline business intelligence."
        }
    },
    "cisco": {
        "pricing_strategy": {
            "summary": "Cisco implemented an 8% increase on Duo Advantage licenses while bundling Splunk observability pipelines under consolidated enterprise licensing agreements.",
            "discussion_point": "Negotiate a unified Cisco-Splunk ELA to leverage combined purchasing power and secure bulk discount margins."
        },
        "ai_cloud_integration": {
            "summary": "Integrating Webex low-bandwidth AI codecs alongside Splunk threat detection telemetry to secure distributed hybrid workspace setups.",
            "discussion_point": "Review Splunk integration timelines to combine network operations with security information monitoring pipelines."
        },
        "product_roadmap": {
            "summary": "Deploying Cisco HyperShield AI security architectures for automated threat prevention in high-density data centers.",
            "discussion_point": "Seek early adoption roadmap timelines for Cisco HyperShield to protect private hybrid cloud environments."
        },
        "security_compliance": {
            "context": "Distributed security architecture post-Splunk merger requires unified access policies and verified zero-trust compliance standards.",
            "discussion_point": "Verify Duo compliance audits under global zero-trust access frameworks for multi-region systems."
        },
        "partnership_opportunities": {
            "context": "Cisco has partnered with NVIDIA to supply pre-configured enterprise AI hardware clusters to corporate clients.",
            "discussion_point": "Evaluate utilizing Cisco-NVIDIA physical hardware packages to host custom private AI training environments."
        }
    },
    "cognizant": {
        "pricing_strategy": {
            "summary": "Cognizant is offering a 15% pricing reduction on initial Neuro AI proof-of-concept phases, while adjusting premium onshore consulting rates up by 5%.",
            "discussion_point": "Secure fixed-cost caps on upcoming digital migration project phases to prevent budget inflation on onshore developer resources."
        },
        "ai_cloud_integration": {
            "summary": "Cognizant Flowsource automates software development cycles, while the Neuro AI platform orchestrates complex multi-agent enterprise decision trees.",
            "discussion_point": "Evaluate deploying Flowsource developer portals to accelerate internal application modernization pipelines."
        },
        "product_roadmap": {
            "summary": "Upskilled 250,000 associates in generative AI applications and launched joint healthcare-focused cloud workflow labs in cooperation with Google.",
            "discussion_point": "Request roadmaps for custom-trained business process automation assets targeting our specific regulatory vertical."
        },
        "security_compliance": {
            "context": "Consulting partners handling cloud migrations must verify ISO 27001 and SOC 2 data protection standards across global delivery hubs.",
            "discussion_point": "Perform annual compliance audits on Cognizant off-shore development centers managing our private databases."
        },
        "partnership_opportunities": {
            "context": "Cognizant has formed a strategic alliance with Microsoft to deliver M365 Copilot migrations at high volume.",
            "discussion_point": "Leverage Cognizant's Microsoft partner status to access discount pricing models for large-scale Copilot rollouts."
        }
    },
    "juniper": {
        "pricing_strategy": {
            "summary": "Juniper raised Mist Wireless LAN annual subscriptions by 6%, while offering 5% package reductions on bulk access switch hardware bundles.",
            "discussion_point": "Negotiate multi-year Mist software subscription price locks in parallel with our upcoming physical campus hardware refresh."
        },
        "ai_cloud_integration": {
            "summary": "Mist AI wired and wireless automation tools proactively troubleshoot physical campus networks, reducing customer support tickets by up to 45%.",
            "discussion_point": "Audit Mist AI helpdesk analytics to verify TCO reductions before extending licensing commitments."
        },
        "product_roadmap": {
            "summary": "Deploying Marvis Virtual Network Assistants for automated video call diagnostic tracking (e.g. Zoom and Microsoft Teams integrations).",
            "discussion_point": "Seek technical details for Marvis integration timelines across our distributed office conference systems."
        },
        "security_compliance": {
            "context": "Enterprise network management requires FedRAMP Moderate cloud authorization and active multi-threat network detection models.",
            "discussion_point": "Verify regulatory compliance frameworks for Mist Cloud network management across global office sites."
        },
        "partnership_opportunities": {
            "context": "Juniper is integrating product lines with HPE post-merger to offer consolidated campus networking solutions.",
            "discussion_point": "Explore joint strategic roadmaps under the HPE-Juniper merger to ensure product continuity for campus fabrics."
        }
    },
    "wipro": {
        "pricing_strategy": {
            "summary": "Wipro introduced flat $7,500 ai360 discovery packages, while raising global managed services engineering rates by 4% on average.",
            "discussion_point": "Leverage flat-rate ai360 workshops to plan migrations before committed spending decisions are made on engineers."
        },
        "ai_cloud_integration": {
            "summary": "Wipro launched its $1B ai360 platform ecosystem and released the Enterprise AI Gateway to secure model governance across corporate networks.",
            "discussion_point": "Assess implementing Wipro's Enterprise AI Gateway to manage API usage and cost caps across multiple LLM accounts."
        },
        "product_roadmap": {
            "summary": "Developing automated code migration workbenches and proprietary healthcare AI diagnostic solutions in collaboration with NVIDIA APIs.",
            "discussion_point": "Request previews of Wipro's custom code translation tools to accelerate legacy server migrations."
        },
        "security_compliance": {
            "context": "Wipro's AI systems are certified under the ISO 42001 artificial intelligence standard, guaranteeing strict compliance structures.",
            "discussion_point": "Verify ISO 42001 certification details for all custom-developed AI integrations deployed in corporate networks."
        },
        "partnership_opportunities": {
            "context": "Wipro has established close co-development partnerships with AWS to build sector-specific generative platforms.",
            "discussion_point": "Evaluate utilizing Wipro's AWS-focused platforms to streamline joint analytics development on secure cloud structures."
        }
    }
}

def migrate():
    mock_dir = BASE_DIR / "mock_data"
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        json_file = vendor_dir / "highlights_vendor_topics.json"
        
        data = MOCK_DATA.get(vendor)
        if data:
            # Structure exactly as highlights_vendor_topics.json containing a serialized JSON string in content
            payload = {
                "content": json.dumps(data),
                "sources": []
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"Successfully migrated highlights_vendor_topics.json for {vendor.upper()}")

if __name__ == "__main__":
    migrate()
    print("Migration complete!")
