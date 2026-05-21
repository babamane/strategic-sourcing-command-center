def generate_risk_alerts(results):

    alerts = []

    for item in results:

        if item["risk_score"] >= 70:

            alerts.append({

                "category":
                    item["risk_category"],

                "severity":
                    "Critical",

                "message":
                    "Immediate executive attention required"
            })

        elif item["risk_score"] >= 50:

            alerts.append({

                "category":
                    item["risk_category"],

                "severity":
                    "High",

                "message":
                    "Risk mitigation required"
            })

    return alerts