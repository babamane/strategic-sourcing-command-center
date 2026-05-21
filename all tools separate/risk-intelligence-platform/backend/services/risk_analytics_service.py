def calculate_vendor_risk_metrics(results: list) -> dict:
    """
    Scoring Engine: Calculates dynamic weighted risk metrics based on 6 active intelligence agents.
    """
    # Map of category to weight
    weights = {
        "Cybersecurity": 0.20,
        "Financial Risk": 0.15,
        "Legal & Sanctions": 0.15,
        "Compliance Risk": 0.10,
        "Geopolitical & Supply Chain": 0.10,
        "ESG Risk": 0.08
    }

    weighted_sum = 0.0
    weight_total = 0.0
    
    # Track the highest risk category
    highest_risk_cat = "Unknown"
    highest_score = -1

    for r in results:
        cat = r["risk_category"]
        score = r["risk_score"]
        
        weight = weights.get(cat, 0.10) # default weight if not matched
        weighted_sum += score * weight
        weight_total += weight
        
        if score > highest_score:
            highest_score = score
            highest_risk_cat = cat

    # Compute overall score
    overall_score = round(weighted_sum / weight_total, 1) if weight_total > 0 else 0.0

    # Map score to severity, tier, and default decision
    if overall_score >= 75:
        severity = "Critical"
        vendor_tier = "Tier 4 (High Risk)"
        decision = "Reject Vendor"
    elif overall_score >= 55:
        severity = "High"
        vendor_tier = "Tier 3 (Moderate-High Risk)"
        decision = "Executive Approval Required"
    elif overall_score >= 40:
        severity = "Medium"
        vendor_tier = "Tier 2 (Moderate Risk)"
        decision = "Conditional Approval"
    else:
        severity = "Low"
        vendor_tier = "Tier 1 (Low Risk)"
        decision = "Approved Vendor"

    # Compute average confidence score
    confidence_scores = [r.get("confidence_score", 85) for r in results]
    avg_confidence = int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 85

    return {
        "overall_risk_score": overall_score,
        "overall_severity": severity,
        "vendor_tier": vendor_tier,
        "procurement_decision": decision,
        "highest_risk_category": highest_risk_cat,
        "highest_risk_score": highest_score,
        "confidence_score": avg_confidence
    }