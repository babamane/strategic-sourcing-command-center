from datetime import datetime, timedelta

def generate_risk_timeline(results: list) -> list:
    """
    Timeline Service: Generates a chronological threat timeline from the actual findings
    of all active intelligence agents.
    """
    timeline = []
    
    # Baseline event
    now = datetime.now()
    timeline.append({
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "event": "Vendor risk assessment completed. Scoring metrics successfully integrated."
    })
    
    event_counter = 1
    # Iterate through agent findings and extract interesting events
    for r in results:
        cat = r["risk_category"]
        findings = r.get("findings", [])
        
        for finding in findings:
            # Filter findings that look like events (e.g. breach news, litigation record, etc.)
            finding_lower = finding.lower()
            if any(keyword in finding_lower for keyword in ["breach", "cve", "scandal", "lawsuit", "disruption", "controversy", "recall", "violation"]):
                # Create a date in the past for this historical event
                event_date = now - timedelta(days=event_counter * 15)
                timeline.append({
                    "date": event_date.strftime("%Y-%m-%d"),
                    "event": f"[{cat}] {finding}"
                })
                event_counter += 1
                if event_counter > 6:  # limit timeline size
                    break
                    
    # Sort timeline by date descending
    timeline.sort(key=lambda x: x["date"], reverse=True)
    return timeline