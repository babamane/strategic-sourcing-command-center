import os
import sys
import json
import re
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.llm_client import LLMClient
from langchain_core.messages import HumanMessage
from tools.briefing_tool import clean_json_content

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

# Pre-crafted rich mock briefings for fallback or direct generation
FALLBACK_BRIEFINGS = {
    "google": {
        "account_summary": {
            "company_overview": "Google is a dominant force in digital advertising, cloud computing (Google Cloud Platform), and AI research. Under parent Alphabet, the company is pivoting aggressively to integrate generative AI across its search and enterprise workspace ecosystems.",
            "key_highlights": [
                "Massive acceleration of Gemini AI models across consumer and cloud portfolios.",
                "Sustained 20%+ year-over-year revenue growth in Google Cloud Platform (GCP).",
                "Increasing focus on custom silicon (TPUs) to optimize AI training and inference costs."
            ]
        },
        "business_performance": {
            "strengths": [
                "Unrivaled data scale and search marketplace dominance.",
                "Pioneering AI research division (Google DeepMind) leading state-of-the-art modeling.",
                "Strong cash position with robust balance sheet allowing rapid capital expenditure."
            ],
            "challenges": [
                "Rising regulatory scrutiny and antitrust cases in US and European markets.",
                "High cloud infrastructure CapEx pressuring operational margins.",
                "Adversarial search competition from Microsoft Bing and emerging AI search engines."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Monetizing AI capabilities in Workspace and Cloud via premium add-on tiers.",
                "Expanding public sector cloud deployment contracts globally.",
                "Scaling autonomous driving partnerships through Waymo monetization."
            ],
            "risks": [
                "Potential disruption to core advertising cash cow by conversational AI queries.",
                "Increased regulatory constraints limiting cross-platform data usage.",
                "Talent migration to specialized generative AI startups."
            ]
        },
        "recommended_actions": [
            "Negotiate multi-year commit discounts on GCP infrastructure services.",
            "Establish co-innovation workshops around Gemini API integrations into internal tools.",
            "Evaluate long-term exposure to Google's cookie deprecation timeline in marketing campaigns."
        ],
        "financial_health": "Google continues to show outstanding financial health, characterized by healthy advertising margins, double-digit cloud expansion, and substantial cash reserves, albeit balanced by high AI-related capital expenditures."
    },
    "microsoft": {
        "account_summary": {
            "company_overview": "Microsoft is a global leader in enterprise software, cloud computing (Azure), and productivity suites. The company is actively capitalizing on its early partnership with OpenAI to embed Copilot across all business segments.",
            "key_highlights": [
                "Azure cloud growth consistently leading hyperscaler expansion rates.",
                "Rapid adoption of Microsoft 365 Copilot within Fortune 500 accounts.",
                "Successful integration of Activision Blizzard bolstering gaming segment revenues."
            ]
        },
        "business_performance": {
            "strengths": [
                "Deep-seated relationship with enterprise IT decision-makers.",
                "Highly diversified revenue mix (cloud, productivity, gaming, personal computing).",
                "Market-leading commercial cloud gross margins exceeding 70%."
            ],
            "challenges": [
                "Increasing energy and hardware supply chain constraints for data center expansion.",
                "Complex integration issues across recently acquired large-scale assets.",
                "Cybersecurity and threat posture improvements requiring intensive operational focus."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Securing long-term sovereign cloud dominance in European markets.",
                "Upselling Copilot licenses to capture higher average revenue per user (ARPU).",
                "Monetizing security-as-a-service through Microsoft Sentinel and Defender."
            ],
            "risks": [
                "Intensified antitrust investigations regarding software bundling practices.",
                "Heavy dependency on OpenAI's foundational model development roadmap.",
                "Potential slowdown in PC hardware refresh cycles impacting OEM revenues."
            ]
        },
        "recommended_actions": [
            "Leverage existing Microsoft Azure commitment to secure volume discounts on Copilot seats.",
            "Review multi-year enterprise agreements (EA) to lock in pricing caps before renewal.",
            "Collaborate on sovereign Azure cloud offerings to comply with regional data governance."
        ],
        "financial_health": "Microsoft displays premier financial health, boasting record-high commercial cloud revenues, exceptionally high operating cash flow, and a strong AAA-rated balance sheet enabling massive capital returns."
    },
    "adobe": {
        "account_summary": {
            "company_overview": "Adobe is the creative industry standard for digital media and marketing software. The company is embedding generative AI (Firefly) into its core Creative Cloud and Experience Cloud applications to expand creator capabilities.",
            "key_highlights": [
                "Strong annual recurring revenue (ARR) growth across Document Cloud and Creative Cloud.",
                "Rapid enterprise adoption of commercial-safe Firefly generative AI tooling.",
                "Increasing transition of traditional design pipelines to collaborative web-first experiences."
            ]
        },
        "business_performance": {
            "strengths": [
                "Dominant industry-standard position in design software (Photoshop, Illustrator).",
                "High customer retention rates driven by deep integration of products.",
                "Highly predictable subscription revenue model with strong gross margins."
            ],
            "challenges": [
                "Fierce competition from lightweight collaborative design platforms.",
                "Transitioning traditional desktop user bases to cloud-native monthly workflows.",
                "Sustaining price premium relative to lower-cost AI alternative platforms."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Upselling enterprise-wide Firefly licenses for brand-compliant content creation.",
                "Expanding Document Cloud usage in legal and medical automated workflows.",
                "Monetizing generative credits for compute-heavy high-resolution design exports."
            ],
            "risks": [
                "Disruption of traditional designer roles by end-user generative AI tools.",
                "Legal liabilities regarding copyright in AI training source datasets.",
                "Macroeconomic impacts forcing SMB clients to reduce creative software budgets."
            ]
        },
        "recommended_actions": [
            "Assess team-wide Creative Cloud utilization to eliminate underused active licenses.",
            "Formulate guidelines for commercial usage of Adobe Firefly to ensure brand indemnity.",
            "Negotiate unified enterprise agreements merging Creative and Document Cloud contracts."
        ],
        "financial_health": "Adobe boasts excellent financial health, characterized by consistent subscription-driven growth, operating margins near 40%, and robust free cash flow supporting continuous share buybacks."
    },
    "cisco": {
        "account_summary": {
            "company_overview": "Cisco is a global leader in networking hardware, telecommunications, and cybersecurity solutions. The company is pivoting toward software subscriptions and security analytics following its acquisition of Splunk.",
            "key_highlights": [
                "Significant enhancement of enterprise observability via Splunk platform integration.",
                "Strategic shift toward software and recurring service revenues over hardware sales.",
                "Launch of specialized AI-ready networking fabric and ethernet solutions."
            ]
        },
        "business_performance": {
            "strengths": [
                "Massive global footprint in critical enterprise network infrastructure.",
                "Broad portfolio spanning campus routing, data center switching, and cybersec.",
                "Highly reliable channels and strong partnerships in enterprise sales."
            ],
            "challenges": [
                "Cyclical spending patterns in telecom carrier and enterprise hardware.",
                "Lengthy integration process for massive acquisitions like Splunk.",
                "Inventory digestions at client sites delaying new product orders."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Cross-selling Splunk security observability to established network clients.",
                "Capturing data center networking demand driven by high-bandwidth AI clusters.",
                "Expanding managed network-as-a-service (NaaS) offerings for enterprise clients."
            ],
            "risks": [
                "Market share erosion from cloud-native software-defined networking (SDN) vendors.",
                "Margin compression under price competitive hardware bidding wars.",
                "Supply chain disruptions impacting physical networking equipment delivery."
            ]
        },
        "recommended_actions": [
            "Evaluate Cisco hardware contracts to replace aging infrastructure with consolidated leases.",
            "Assess joint security offerings under the unified Cisco-Splunk observability roadmap.",
            "Initiate a proof-of-concept for AI-optimized ethernet fabric in high-throughput environments."
        ],
        "financial_health": "Cisco maintains solid financial health with reliable cash flow, consistent dividend payouts, and a strong balance sheet supporting massive software integrations."
    },
    "salesforce": {
        "account_summary": {
            "company_overview": "Salesforce is the leading global provider of customer relationship management (CRM) software. The company is currently driving the adoption of autonomous AI agents (Agentforce) across sales, service, and marketing clouds.",
            "key_highlights": [
                "Rapid scaling of Agentforce autonomous agents replacing legacy chatbots.",
                "Expanding operating margins driven by restructuring and strict capital discipline.",
                "Strong momentum in multi-cloud enterprise agreements combining core suites."
            ]
        },
        "business_performance": {
            "strengths": [
                "Uncontested leader in cloud CRM with massive client ecosystem.",
                "Highly effective cross-selling model across Sales, Service, and Marketing clouds.",
                "High customer switching costs due to custom integrations and workflows."
            ],
            "challenges": [
                "Slowing growth in core CRM segments as markets approach maturity.",
                "Customer pushback against complex pricing and product bundling.",
                "Fierce competition in mid-market segments from agile, specialized CRM systems."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Upselling autonomous service agents to lower operational customer support costs.",
                "Monetizing unified customer data through Salesforce Data Cloud.",
                "Expanding industry-specific cloud verticals (Health, Financial Services)."
            ],
            "risks": [
                "Potential decline in seat-based license pricing due to AI agent efficiencies.",
                "Macroeconomic pressures slowing down long-term digital transformations.",
                "Customer churn in smaller accounts sensitive to rising subscription costs."
            ]
        },
        "recommended_actions": [
            "Audit current seat utilization to prepare for contract renewals under potential agent transitions.",
            "Benchmark custom Salesforce integrations against industry standards to reduce maintenance costs.",
            "Evaluate Data Cloud capabilities to consolidate siloed customer information systems."
        ],
        "financial_health": "Salesforce possesses strong financial health, with marked improvement in operating margins (exceeding 30% on a non-GAAP basis) and exceptional free cash flow generation."
    },
    "cognizant": {
        "account_summary": {
            "company_overview": "Cognizant is a leading provider of information technology, consulting, and business process outsourcing services. The company is focusing on scaling generative AI solutions to drive client digital transformation agendas.",
            "key_highlights": [
                "Expansion of strategic AI alliances with Microsoft, Google Cloud, and AWS.",
                "Sustained booking momentum driven by large-scale enterprise modernization deals.",
                "Active investments in upskilling global associate base on advanced AI frameworks."
            ]
        },
        "business_performance": {
            "strengths": [
                "Deep domain expertise in healthcare, financial services, and life sciences.",
                "Highly competitive offshore delivery model based out of India.",
                "Long-standing relationships with global Fortune 500 customers."
            ],
            "challenges": [
                "Intense pricing pressure from clients optimizing discretionary IT spend.",
                "Competitive talent market demanding continuous compensation adjustments.",
                "Slower decision-making cycles on large discretionary consulting engagements."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Accelerating legacy mainframe-to-cloud migrations using AI translation tools.",
                "Expanding digital engineering consulting services in European markets.",
                "Developing customized industry-specific generative AI agent workflows."
            ],
            "risks": [
                "Potential automation of basic business process services reducing workforce demand.",
                "Geopolitical and visa regulation changes impacting global talent mobility.",
                "Margin compression due to wage inflation in key delivery locations."
            ]
        },
        "recommended_actions": [
            "Negotiate outcome-based pricing models for software development and IT maintenance contracts.",
            "Engage Cognizant for proofs-of-concept utilizing their pre-built AI delivery accelerators.",
            "Align upcoming project pipelines with offshore delivery slots to optimize resource rates."
        ],
        "financial_health": "Cognizant maintains solid financial health, characterized by consistent operating margins, healthy free cash flow conversion, and a robust capital allocation plan focusing on acquisitions and share buybacks."
    },
    "juniper": {
        "account_summary": {
            "company_overview": "Juniper Networks is a prominent developer of high-performance networking products, software, and services. The company is recognized for its AI-native networking engine (Mist AI) and is in the process of being acquired by HPE.",
            "key_highlights": [
                "High growth and industry recognition for Mist AI-driven enterprise campus and branch solutions.",
                "Pending acquisition by Hewlett Packard Enterprise (HPE) to consolidate hybrid cloud network portfolios.",
                "Expanding footprint in massive AI data center networking and routing."
            ]
        },
        "business_performance": {
            "strengths": [
                "Pioneering Mist AI platform offering superior network automation and diagnostics.",
                "Strong reputation in high-throughput service provider routing and switching.",
                "Robust security and cloud-integrated fabric solutions."
            ],
            "challenges": [
                "Integration and operational uncertainties regarding the pending HPE acquisition.",
                "Concentration of revenue among a few massive cloud hyperscaler accounts.",
                "Fierce competition from dominant enterprise networking giants."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Leveraging HPE's massive global channel sales machine post-merger.",
                "Capitalizing on AI cloud cluster deployments requiring specialized networking.",
                "Upselling automated security operations powered by AI."
            ],
            "risks": [
                "Potential loss of customers due to roadmap confusion during the HPE merger.",
                "Long sales cycles in telecom and service provider sectors.",
                "Supply chain constraints in specialized custom silicon components."
            ]
        },
        "recommended_actions": [
            "Request roadmap guarantees and price protection agreements in light of the HPE acquisition.",
            "Pilot Juniper Mist AI-driven wireless access points to evaluate automated troubleshooting capabilities.",
            "Secure volume discounts on high-performance data center switches during transitional merger phases."
        ],
        "financial_health": "Juniper enjoys stable financial health, with dependable enterprise customer growth and consistent gross margins, albeit under current transactional conditions related to the pending acquisition."
    },
    "wipro": {
        "account_summary": {
            "company_overview": "Wipro is a prominent global information technology, consulting, and business process services company. Headquartered in India, Wipro is driving its 'ai360' ecosystem to embed AI across all client solutions and delivery platforms.",
            "key_highlights": [
                "Investment of $1 billion in 'ai360' to train all employees and integrate AI capabilities.",
                "Steady expansion in large-deal bookings across cloud and cybersecurity spaces.",
                "Executive leadership shifts focused on optimizing operational efficiency and client retention."
            ]
        },
        "business_performance": {
            "strengths": [
                "Broad global delivery footprint with cost-competitive offshore hubs.",
                "Specialized capabilities in cloud transformation, cybersecurity, and engineering services.",
                "Deep client relationships within banking, manufacturing, and energy verticals."
            ],
            "challenges": [
                "Restructuring and leadership transition adjustments impacting short-term growth.",
                "Intensified competitive pressure from both tier-1 Indian peers and boutique agencies.",
                "Customer budget constraints slowing down discretionary IT project executions."
            ]
        },
        "opportunities_risks": {
            "opportunities": [
                "Upselling AI-integrated application management services to capture productivity gains.",
                "Expanding cybersecurity consulting amidst rising global digital vulnerabilities.",
                "Capitalizing on green IT and sustainable technology consultancy services."
            ],
            "risks": [
                "High attrition rates in critical tech skill domains.",
                "Potential client-side demands for rate cuts driven by AI automation efficiencies.",
                "Macroeconomic downturns in key Western geographies impacting tech spends."
            ]
        },
        "recommended_actions": [
            "Initiate discussions to co-invest in AI prototypes under the Wipro ai360 framework.",
            "Review service level agreements (SLAs) to capture productivity improvements from AI tools.",
            "Optimize offshore-onshore staffing ratios across current application maintenance pipelines."
        ],
        "financial_health": "Wipro exhibits stable financial health, backed by robust cash flow, healthy operating margins around 16%, and a strong history of regular dividends and capital return programs."
    }
}

def migrate_mock_files():
    mock_dir = BASE_DIR / "mock_data"
    
    # Try initializing the LLM client
    llm = None
    try:
        llm = LLMClient().get_llm()
        print(f"LLM Client initialized successfully. Will attempt AI-powered migration.")
    except Exception as e:
        print(f"LLM Client failed to initialize ({e}). Proceeding with pre-crafted high-quality briefs.")
        
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        md_file = vendor_dir / "briefing.md"
        json_file = vendor_dir / "briefing.json"
        
        print(f"--- Processing {vendor.upper()} ---")
        
        md_content = ""
        if md_file.exists():
            with open(md_file, "r", encoding="utf-8") as f:
                md_content = f.read()
            print(f"Read briefing.md ({len(md_content)} characters)")
        else:
            print(f"Warning: briefing.md not found for {vendor}")

        success = False
        if llm and md_content:
            try:
                # Ask LLM to translate
                prompt = f"""You are an AI business analyst assistant. Your task is to convert the following legacy briefing markdown file into a highly professional structured JSON briefing document.
                
Follow the user's new format and guidelines exactly.

OUTPUT FORMAT:
{{
  "account_summary": {{
    "company_overview": "2-3 sentence concise overview of the company, business model, and current business context.",
    "key_highlights": [
      "Important highlight 1",
      "Important highlight 2",
      "Important highlight 3"
    ]
  }},
  "business_performance": {{
    "strengths": [
      "Business strength 1",
      "Business strength 2",
      "Business strength 3"
    ],
    "challenges": [
      "Business challenge 1",
      "Business challenge 2",
      "Business challenge 3"
    ]
  }},
  "opportunities_risks": {{
    "opportunities": [
      "Strategic opportunity 1",
      "Strategic opportunity 2",
      "Strategic opportunity 3 (if applicable)"
    ],
    "risks": [
      "Risk or concern 1 to be aware of",
      "Risk or concern 2",
      "Risk or concern 3 (if applicable)"
    ]
  }},
  "recommended_actions": [
    "Recommended action 1 - specific next step",
    "Recommended action 2 - specific next step",
    "Recommended action 3 - specific next step"
  ],
  "financial_health": "Write 2-3 concise sentences summarizing the overall financial/business health based on the available data."
}}

GUIDELINES:
- Each point should be concise (1-2 sentences maximum)
- Focus on actionable and executive-level insights
- Maintain professional and neutral business language
- Return ONLY the JSON object
- Do not include markdown formatting, explanations, or additional text outside the JSON

LEGACY MARKDOWN DATA:
{md_content}
"""
                response = llm.invoke([HumanMessage(content=prompt)])
                cleaned = clean_json_content(response.content.strip())
                
                # Verify JSON
                parsed = json.loads(cleaned)
                
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=2)
                print(f"Successfully generated briefing.json using AI.")
                success = True
            except Exception as e:
                print(f"AI conversion failed for {vendor} ({e}). Falling back to template.")

        if not success:
            # Generate using rich pre-crafted templates
            fallback_data = FALLBACK_BRIEFINGS.get(vendor)
            if not fallback_data:
                # Default generic template
                fallback_data = {
                    "account_summary": {
                        "company_overview": f"A leading technology enterprise, {vendor} continues to drive innovation in its sector.",
                        "key_highlights": [
                            "Sustained core product dominance in the global market.",
                            "Active transition toward AI-powered features and service portfolios.",
                            "Robust balance sheet supporting long-term strategic investments."
                        ]
                    },
                    "business_performance": {
                        "strengths": [
                            "Strong brand equity and customer loyalty across standard markets.",
                            "Diverse revenue streams reducing dependency on single business segments.",
                            "Highly capable research and development capabilities."
                        ],
                        "challenges": [
                            "Rising operational costs due to infrastructure and talent acquisitions.",
                            "Macroeconomic tailwinds impacting long-term customer budgets.",
                            "Fierce competitive landscape with fast-moving direct competitors."
                        ]
                    },
                    "opportunities_risks": {
                        "opportunities": [
                            "Expansion into emerging AI and enterprise intelligence markets.",
                            "Deeper penetration of existing customer accounts via bundling offerings.",
                            "Strategic partnerships to unlock novel co-innovation tracks."
                        ],
                        "risks": [
                            "Regulatory hurdles and evolving compliance directives globally.",
                            "Potential margin compression under high infrastructure spend.",
                            "Integration friction for next-generation products into traditional pipelines."
                        ]
                    },
                    "recommended_actions": [
                        f"Establish a joint roadmap steering committee with {vendor} key accounts.",
                        "Conduct a detailed review of current and future multi-year pricing models.",
                        "Identify high-value integration points to leverage new AI capabilities."
                    ],
                    "financial_health": f"The overall financial health for {vendor} remains highly resilient, marked by steady revenue patterns and active capital allocation towards future growth vectors."
                }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(fallback_data, f, indent=2)
            print(f"Successfully generated briefing.json from pre-crafted template.")
            
        # Delete old md file
        if md_file.exists():
            try:
                os.remove(md_file)
                print(f"Removed legacy briefing.md")
            except Exception as e:
                print(f"Could not remove legacy briefing.md: {e}")

if __name__ == "__main__":
    migrate_mock_files()
    print("Migration finished!")
