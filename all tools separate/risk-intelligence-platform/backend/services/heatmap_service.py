def generate_heatmap_data(results):

    heatmap = []

    for item in results:

        risk_score = item[
            "risk_score"
        ]

        intensity = "Low"

        if risk_score >= 70:

            intensity = "Critical"

        elif risk_score >= 50:

            intensity = "High"

        elif risk_score >= 35:

            intensity = "Medium"

        heatmap.append({

            "category":
                item["risk_category"],

            "score":
                risk_score,

            "intensity":
                intensity
        })

    return heatmap