"""Stage 1 — Supplier Discovery Agent."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SEARCH_MAX_RESULTS
from backend.schemas import DiscoveryResult

# Maps product/brand names AND common direct-name inputs to canonical company name
_COMPANY_MAP = {
    "claude":          "Anthropic",
    "anthropic":       "Anthropic",
    "chatgpt":         "OpenAI",
    "openai":          "OpenAI",
    "open ai":         "OpenAI",
    "gpt-4":           "OpenAI",
    "gpt4":            "OpenAI",
    "gpt":             "OpenAI",
    "o1":              "OpenAI",
    "gemini":          "Google DeepMind",
    "google deepmind": "Google DeepMind",
    "deepmind":        "Google DeepMind",
    "google":          "Google DeepMind",
    "bard":            "Google DeepMind",
    "copilot":         "Microsoft",
    "microsoft":       "Microsoft",
    "llama":           "Meta AI",
    "meta":            "Meta AI",
    "meta ai":         "Meta AI",
    "mistral":         "Mistral AI",
    "mistral ai":      "Mistral AI",
    "salesforce":      "Salesforce",
    "servicenow":      "ServiceNow",
    "workday":         "Workday",
    "hubspot":         "HubSpot",
    "zendesk":         "Zendesk",
    "slack":           "Slack (Salesforce)",
}

# Static reference URLs shown when DuckDuckGo returns no results
_STATIC_SOURCES = {
    "Anthropic":       ["https://www.anthropic.com", "https://docs.anthropic.com/en/docs", "https://www.crunchbase.com/organization/anthropic", "https://techcrunch.com/tag/anthropic/"],
    "OpenAI":          ["https://openai.com", "https://platform.openai.com/docs", "https://www.crunchbase.com/organization/openai", "https://techcrunch.com/tag/openai/"],
    "Google DeepMind": ["https://deepmind.google", "https://ai.google.dev", "https://cloud.google.com/vertex-ai", "https://www.crunchbase.com/organization/deepmind"],
    "Microsoft":       ["https://www.microsoft.com/en-us/ai", "https://azure.microsoft.com/en-us/products/ai-services", "https://www.crunchbase.com/organization/microsoft"],
    "Meta AI":         ["https://ai.meta.com", "https://llama.meta.com", "https://www.crunchbase.com/organization/facebook"],
    "Mistral AI":      ["https://mistral.ai", "https://docs.mistral.ai", "https://www.crunchbase.com/organization/mistral-ai"],
    "Salesforce":      ["https://www.salesforce.com", "https://investor.salesforce.com", "https://www.crunchbase.com/organization/salesforce"],
    "ServiceNow":      ["https://www.servicenow.com", "https://investor.servicenow.com", "https://www.crunchbase.com/organization/servicenow"],
    "Workday":         ["https://www.workday.com", "https://investor.workday.com", "https://www.crunchbase.com/organization/workday"],
}

def _resolve_company(vendor_name: str) -> str:
    """Map product/brand names to their parent company for accurate searches."""
    key = vendor_name.lower().strip()
    if key in _COMPANY_MAP:
        return _COMPANY_MAP[key]
    # Title-case the input as last resort so "openai" → "Openai" becomes a passable search term
    return vendor_name.strip().title()


def _ddg_search(vendor_name: str) -> tuple[str, list[str], str]:
    company = _resolve_company(vendor_name)
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(
            f'"{company}" company profile revenue employees funding leadership products technology 2024 2025',
            max_results=SEARCH_MAX_RESULTS,
        ))
        context = "\n\n".join(f"[{r.get('href','')}]\n{r.get('body','')}" for r in results)
        sources = [r.get("href", "") for r in results]
        return context, sources, company
    except Exception as e:
        return f"Search unavailable: {e}", [], company


def _llm_profile(vendor_name: str, company_name: str, web_context: str) -> dict | None:
    try:
        from langchain_ollama import OllamaLLM
        llm    = OllamaLLM(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0)
        prompt = f"""You are a senior supplier discovery analyst. Build a comprehensive vendor profile ONLY for "{company_name}".

CRITICAL: Every field in your response must describe "{company_name}" specifically.
Do NOT include information about competitors, related companies, or any other vendor.
If the search results mention other companies in comparison, ignore those comparisons and focus only on "{company_name}".

=== Web Intelligence ===
{web_context or f'{company_name} is an enterprise technology company.'}
========================

Return ONLY a valid JSON object. All fields must be specific to "{company_name}":
{{
  "company_summary":      "<3-4 sentences about {company_name} specifically>",
  "founded":              "<year {company_name} was founded>",
  "headquarters":         "<{company_name} headquarters city, country>",
  "employees":            "<{company_name} employee count range>",
  "market_segment":       "<{company_name} target market>",
  "recent_funding":       "<{company_name} latest funding round>",
  "market_position":      "<{company_name} competitive position, 1-2 sentences>",
  "revenue_estimate":     "<{company_name} ARR or revenue estimate>",
  "products":             ["<{company_name} product 1>", "<{company_name} product 2>"],
  "product_descriptions": {{"<product 1>": "<description>", "<product 2>": "<description>"}},
  "tech_stack":           ["<technology>", "<cloud provider>", "<language>"],
  "key_executives":       ["<CEO of {company_name}> — CEO", "<CTO of {company_name}> — CTO"],
  "main_competitors":     ["<competitor of {company_name}>", "<competitor>"],
  "customer_segments":    ["<segment>", "<segment>"],
  "geographic_presence":  ["<region>", "<region>"],
  "recent_news":          ["<recent {company_name} news item>", "<news item>"],
  "analyst_rating":       "<analyst rating for {company_name}>",
  "business_model":       "<{company_name} business model>",
  "growth_rate":          "<{company_name} growth rate>"
}}"""
        raw  = llm.invoke(prompt)
        s, e = raw.find("{"), raw.rfind("}") + 1
        if s == -1:
            return None
        parsed = json.loads(raw[s:e])
        # Validate: if the company summary doesn't mention the company name, reject
        summary = parsed.get("company_summary", "").lower()
        if company_name.lower().split()[0] not in summary and vendor_name.lower() not in summary:
            return None
        return parsed
    except Exception:
        return None


def _fallback(vendor_name: str, company_name: str) -> dict:
    # Vendor-specific accurate data for common vendors
    known = {
        "Anthropic": {
            "company_summary":     "Anthropic is an AI safety company founded in 2021, focused on building reliable, interpretable, and steerable AI systems. The company is best known for Claude, its family of large language models. Anthropic conducts frontier AI research and offers Claude as an enterprise API for developers and businesses.",
            "founded":             "2021",
            "headquarters":        "San Francisco, CA, USA",
            "employees":           "500–1,000",
            "market_segment":      "Enterprise AI / AI Safety Research",
            "recent_funding":      "Series E — $2.75B (Google, Amazon, 2024)",
            "market_position":     "One of the leading frontier AI labs alongside OpenAI and Google DeepMind, positioned on AI safety and enterprise reliability.",
            "revenue_estimate":    "$200M–$500M ARR (estimated)",
            "products":            ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude API", "Claude.ai"],
            "product_descriptions": {
                "Claude 3.5 Sonnet": "State-of-the-art LLM balancing intelligence and speed, outperforming GPT-4o on key benchmarks.",
                "Claude 3 Opus":     "Most powerful Claude model for complex reasoning and analysis tasks.",
                "Claude API":        "Enterprise API for integrating Claude into products and workflows.",
                "Claude.ai":         "Consumer and Teams interface for direct Claude access.",
            },
            "tech_stack":          ["AWS", "Google Cloud", "Python", "PyTorch", "Constitutional AI"],
            "key_executives":      [
                "Dario Amodei — CEO & Co-founder (former VP Research, OpenAI)",
                "Daniela Amodei — President & Co-founder",
                "Tom Brown — VP Research",
                "Chris Olah — Research Scientist (interpretability)",
            ],
            "main_competitors":    ["OpenAI (GPT-4)", "Google DeepMind (Gemini)", "Meta AI (Llama)", "Mistral AI"],
            "customer_segments":   ["Enterprise Software", "Developer Tools", "Healthcare", "Legal & Compliance", "Financial Services"],
            "geographic_presence": ["North America (primary)", "Europe (growing)", "APAC (emerging)"],
            "recent_news":         [
                "Claude 3.5 Sonnet released — sets new benchmark on coding and reasoning (June 2024)",
                "Amazon invests additional $2.75B in Anthropic, deepening AWS partnership (March 2024)",
                "Anthropic launches Claude Teams plan for business use (2024)",
                "Constitutional AI research published — advances in AI alignment techniques",
            ],
            "analyst_rating":      "Leader — Forrester Wave: AI Foundation Models Q3 2024",
            "business_model":      "API usage-based pricing + Claude.ai subscription (Free/Pro/Teams/Enterprise)",
            "growth_rate":         "~200% YoY (estimated from AWS/Google investment signals)",
        },
        "OpenAI": {
            "company_summary":     "OpenAI is an AI research and deployment company founded in 2015, creator of the GPT series of large language models and ChatGPT. The company operates as a capped-profit entity backed by Microsoft and offers its models via API and consumer products. OpenAI is the market leader in generative AI with the largest installed base.",
            "founded":             "2015",
            "headquarters":        "San Francisco, CA, USA",
            "employees":           "1,500–3,000",
            "market_segment":      "Enterprise AI / Consumer AI / Developer Tools",
            "recent_funding":      "Series at $157B valuation — $6.6B raised (October 2024)",
            "market_position":     "Market leader in generative AI with ChatGPT as the most widely used AI product globally.",
            "revenue_estimate":    "$3.4B ARR (2024, reported)",
            "products":            ["GPT-4o", "ChatGPT", "DALL-E 3", "Whisper", "Sora", "Assistants API"],
            "product_descriptions": {
                "GPT-4o":        "Flagship multimodal model handling text, vision, and audio.",
                "ChatGPT":       "Consumer and enterprise AI assistant with 100M+ weekly active users.",
                "DALL-E 3":      "State-of-the-art image generation model.",
                "Assistants API": "API for building custom AI assistants with tools and memory.",
            },
            "tech_stack":          ["Microsoft Azure", "Python", "PyTorch", "RLHF", "Kubernetes"],
            "key_executives":      [
                "Sam Altman — CEO",
                "Greg Brockman — President & Co-founder",
                "Mira Murati — Former CTO (departed 2024)",
                "Brad Lightcap — COO",
            ],
            "main_competitors":    ["Anthropic (Claude)", "Google DeepMind (Gemini)", "Meta AI (Llama)", "Mistral AI"],
            "customer_segments":   ["Enterprise", "Developers", "Education", "Healthcare", "Media & Content"],
            "geographic_presence": ["North America (dominant)", "Europe", "APAC", "Middle East (growing)"],
            "recent_news":         [
                "GPT-4o released with real-time voice and vision capabilities (May 2024)",
                "Raised $6.6B at $157B valuation in October 2024",
                "Launched ChatGPT Enterprise with SOC 2 compliance (2024)",
                "o1 reasoning model released, excels at complex problem-solving (September 2024)",
            ],
            "analyst_rating":      "Leader — Gartner Magic Quadrant for Cloud AI Developer Services 2024",
            "business_model":      "API token-based pricing + ChatGPT subscription (Free/Plus/Team/Enterprise)",
            "growth_rate":         "~150% YoY ARR growth (reported)",
        },
        "Google DeepMind": {
            "company_summary":     "Google DeepMind is Alphabet's AI research laboratory formed by the 2023 merger of Google Brain and DeepMind. It is the organisation behind Gemini, AlphaFold, and AlphaCode, and is one of the world's leading AI research institutions. Google DeepMind develops frontier AI models and deploys them through Google Cloud and Google products globally.",
            "founded":             "2010 (DeepMind); merged with Google Brain in 2023",
            "headquarters":        "London, UK (DeepMind) / Mountain View, CA, USA (Google Brain)",
            "employees":           "3,000–5,000",
            "market_segment":      "Enterprise AI / Consumer AI / AI Research",
            "recent_funding":      "Subsidiary of Alphabet Inc. (NASDAQ: GOOGL, ~$1.9T market cap, 2024)",
            "market_position":     "One of the world's leading AI research labs; Gemini competes directly with GPT-4o and Claude 3.5 in enterprise and developer markets.",
            "revenue_estimate":    "Contributes to Google Cloud AI revenue ($33.2B segment, 2024); Gemini API revenue not separately disclosed",
            "products":            ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "Gemini API", "Google AI Studio", "AlphaFold 3", "AlphaCode 2"],
            "product_descriptions": {
                "Gemini 1.5 Pro":   "Flagship multimodal model with 1M token context window for enterprise reasoning and analysis.",
                "Gemini 1.5 Flash": "Fast, cost-efficient model optimised for high-volume enterprise workloads.",
                "Gemini API":       "Enterprise API for integrating Gemini models into products and workflows via Google Cloud.",
                "Google AI Studio": "Developer platform for prototyping and deploying Gemini-powered applications.",
                "AlphaFold 3":      "AI system for protein structure prediction; transforming drug discovery and life sciences.",
                "AlphaCode 2":      "AI coding system competing in competitive programming; integrated into Gemini Code Assist.",
            },
            "tech_stack":          ["Google Cloud (TPUs)", "TensorFlow", "JAX", "Python", "Kubernetes", "Spanner"],
            "key_executives":      [
                "Demis Hassabis — CEO, Google DeepMind & Co-founder",
                "Koray Kavukcuoglu — CTO, Google DeepMind",
                "Oriol Vinyals — VP Research, Google DeepMind",
                "Jeff Dean — Chief Scientist, Google (former Google Brain lead)",
                "Sundar Pichai — CEO, Alphabet (parent company)",
            ],
            "main_competitors":    ["OpenAI (GPT-4o / ChatGPT)", "Anthropic (Claude)", "Meta AI (Llama)", "Mistral AI"],
            "customer_segments":   ["Enterprise Software", "Healthcare & Life Sciences", "Developer Tools", "Government", "Financial Services", "Education"],
            "geographic_presence": ["Global — 40+ Google Cloud regions", "North America (dominant)", "Europe", "APAC", "Middle East"],
            "recent_news":         [
                "Gemini 1.5 Pro released with 1M token context window — industry-leading long-context capability (2024)",
                "AlphaFold 3 published in Nature — predicts structure of all molecules of life (May 2024)",
                "Google DeepMind and Google Brain officially merged under Demis Hassabis (April 2023)",
                "Gemini API made generally available via Google Cloud Vertex AI and Google AI Studio (2024)",
                "AlphaCode 2 achieves top 15% in competitive programming — integrated into Gemini Code Assist",
            ],
            "analyst_rating":      "Leader — Gartner Magic Quadrant for Cloud AI Developer Services 2024; Forrester Wave AI Foundation Models Leader",
            "business_model":      "Gemini API usage-based pricing via Google Cloud + Google Workspace AI add-ons + Google One AI Premium subscription",
            "growth_rate":         "Google Cloud segment growing 28% YoY (Q4 2024); Gemini API adoption accelerating post-GA launch",
        },
        "Microsoft": {
            "company_summary":     "Microsoft is a global technology corporation and the world's largest software company by revenue. Its AI strategy is anchored by a $13B strategic partnership with OpenAI and the integration of Copilot AI across Microsoft 365, Azure, GitHub, and Dynamics 365. Microsoft Azure is the second-largest cloud platform globally.",
            "founded":             "1975",
            "headquarters":        "Redmond, WA, USA",
            "employees":           "221,000+",
            "market_segment":      "Enterprise Software / Cloud Computing / AI Infrastructure",
            "recent_funding":      "Public company (NASDAQ: MSFT, ~$3.1T market cap, 2024)",
            "market_position":     "Dominant enterprise software vendor; Azure is #2 cloud globally; Copilot is the leading enterprise AI assistant suite.",
            "revenue_estimate":    "$245B total revenue FY2024 (reported); Azure ~$105B run rate",
            "products":            ["Microsoft 365 Copilot", "Azure OpenAI Service", "GitHub Copilot", "Dynamics 365 Copilot", "Azure AI Studio"],
            "product_descriptions": {
                "Microsoft 365 Copilot": "AI assistant integrated across Word, Excel, Teams, Outlook powered by GPT-4.",
                "Azure OpenAI Service":  "Enterprise-grade access to OpenAI models (GPT-4o, DALL-E, Whisper) via Azure.",
                "GitHub Copilot":        "AI coding assistant with 1.8M+ paid subscribers; integrates into VS Code and JetBrains.",
                "Dynamics 365 Copilot":  "AI embedded across CRM and ERP workflows.",
            },
            "tech_stack":          ["Microsoft Azure", "C#", ".NET", "Python", "TypeScript", "OpenAI GPT-4"],
            "key_executives":      [
                "Satya Nadella — CEO & Chairman",
                "Amy Hood — CFO & Executive VP",
                "Kevin Scott — CTO & Executive VP of AI",
                "Scott Guthrie — EVP, Cloud & AI",
                "Mustafa Suleyman — CEO, Microsoft AI (former DeepMind co-founder)",
            ],
            "main_competitors":    ["Google Workspace / DeepMind", "Salesforce", "Amazon AWS", "Oracle", "SAP"],
            "customer_segments":   ["Enterprise", "Government", "Education", "SMB", "Developers", "Healthcare"],
            "geographic_presence": ["Global — 60+ Azure regions", "North America (dominant)", "Europe", "APAC", "Middle East & Africa"],
            "recent_news":         [
                "Microsoft 365 Copilot reached 1M+ enterprise users in 2024 — fastest enterprise AI adoption on record",
                "Committed additional $13B to OpenAI; deepened Azure AI integration (2024)",
                "Mustafa Suleyman (DeepMind co-founder) appointed CEO of Microsoft AI division (2024)",
                "GitHub Copilot surpassed 1.8M paid subscribers; expanded to Copilot Workspace (2024)",
            ],
            "analyst_rating":      "Leader — Gartner Magic Quadrant for Cloud AI Developer Services, Strategic Cloud Platforms, and Unified Communications 2024",
            "business_model":      "SaaS subscription (M365, Dynamics) + Azure consumption-based cloud + per-seat Copilot add-on ($30/user/month)",
            "growth_rate":         "~15% YoY total revenue; Azure growing 31% YoY (Q4 FY2024)",
        },
    }

    # Case-insensitive lookup so "openai" hits "OpenAI" etc.
    match = next((k for k in known if k.lower() == company_name.lower()), None)
    data = known.get(match or company_name, {
        "company_summary":     f"{company_name} is an established enterprise technology vendor offering cloud-native business solutions.",
        "founded":             "Unknown",
        "headquarters":        "Unknown",
        "employees":           "Unknown",
        "market_segment":      "Enterprise",
        "recent_funding":      "Undisclosed",
        "market_position":     f"{company_name} is a vendor operating in the enterprise software market.",
        "revenue_estimate":    "Not publicly disclosed",
        "products":            [f"{company_name} Platform"],
        "product_descriptions": {f"{company_name} Platform": f"Core platform offering from {company_name}."},
        "tech_stack":          ["Cloud infrastructure", "API-first architecture"],
        "key_executives":      [f"Details not publicly available — contact {company_name} directly"],
        "main_competitors":    ["To be researched"],
        "customer_segments":   ["Enterprise", "Mid-Market"],
        "geographic_presence": ["North America"],
        "recent_news":         [f"Visit {company_name}'s official website for the latest updates"],
        "analyst_rating":      "Not publicly rated",
        "business_model":      "SaaS subscription",
        "growth_rate":         "Not publicly disclosed",
    })
    return data


def run_discovery(vendor_name: str) -> DiscoveryResult:
    web_context, sources, company_name = _ddg_search(vendor_name)
    data = _llm_profile(vendor_name, company_name, web_context) or _fallback(vendor_name, company_name)
    # Merge live sources with static fallback so panel always shows something
    static = _STATIC_SOURCES.get(company_name, [])
    data["sources"] = list(dict.fromkeys(sources + static))  # dedupe, live first
    return DiscoveryResult(**data)
