def generate_portfolio_metrics(
    results
):

    high_risk = 0

    medium_risk = 0

    low_risk = 0

    for item in results:

        severity = item[
            "severity"
        ]

        if severity == "High":

            high_risk += 1

        elif severity == "Medium":

            medium_risk += 1

        else:

            low_risk += 1

    return {

        "high_risk_categories":
            high_risk,

        "medium_risk_categories":
            medium_risk,

        "low_risk_categories":
            low_risk,

        "total_categories":
            len(results)
    }