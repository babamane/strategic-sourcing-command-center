import asyncio

# Import the 6 core risk and profile agents
from agents.cybersecurity_agent import analyze_cybersecurity_risk
from agents.financial_agent import analyze_financial_risk
from agents.esg_agent import analyze_esg_risk
from agents.geopolitical_agent import analyze_geopolitical_risk
from agents.legal_agent import analyze_legal_risk
from agents.compliance_agent import analyze_compliance_risk

# Import services
from services.report_service import generate_ai_report
from services.mitigation_service import generate_mitigation_plan
from services.risk_analytics_service import calculate_vendor_risk_metrics
from services.heatmap_service import generate_heatmap_data
from services.portfolio_service import generate_portfolio_metrics
from services.alert_service import generate_risk_alerts
from services.vendor_comparison_service import generate_vendor_benchmark
from services.timeline_service import generate_risk_timeline


def _generate_reports_sequentially(threat_vectors):
    executive_summary = generate_ai_report(threat_vectors)
    mitigation_plan = generate_mitigation_plan(threat_vectors)
    return executive_summary, mitigation_plan


async def run_risk_analysis(vendor_data: dict) -> dict:
    """
    Multi-agent Orchestrator: Concurrently executes the 9 intelligence agents,
    runs the scoring engine, and invokes the procurement decision agent.
    """
    # ===================================
    # 1. RUN 6 INTELLIGENCE AGENTS (PARALLEL)
    # ===================================
    results = await asyncio.gather(
        analyze_cybersecurity_risk(vendor_data),
        analyze_financial_risk(vendor_data),
        analyze_esg_risk(vendor_data),
        analyze_geopolitical_risk(vendor_data),
        analyze_legal_risk(vendor_data),
        analyze_compliance_risk(vendor_data)
    )

    # Convert results tuple to a list
    results = list(results)

    # ===================================
    # 2. RUN WEIGHTED SCORING ENGINE
    # ===================================
    metrics = calculate_vendor_risk_metrics(results)
    
    # ===================================
    # 3. ENTERPRISE ANALYTICS & REPORTS
    # ===================================
    threat_vectors = results
    
    heatmap = generate_heatmap_data(threat_vectors)
    portfolio_metrics = generate_portfolio_metrics(threat_vectors)
    alerts = generate_risk_alerts(threat_vectors)
    benchmark = generate_vendor_benchmark(threat_vectors)
    timeline = generate_risk_timeline(threat_vectors)

    # Generate enterprise AI reports sequentially in a single background thread to prevent Ollama CPU deadlock/thrashing
    executive_summary, mitigation_plan = await asyncio.to_thread(_generate_reports_sequentially, threat_vectors)

    return {
        "overall_assessment": metrics,
        "heatmap": heatmap,
        "portfolio_metrics": portfolio_metrics,
        "alerts": alerts,
        "benchmark": benchmark,
        "timeline": timeline,
        "executive_summary": executive_summary,
        "mitigation_plan": mitigation_plan,
        "results": results  # contains the 6 active agents
    }