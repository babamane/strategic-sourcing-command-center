def generate_vendor_benchmark(
    results
):

    benchmark = []

    industry_average = 45

    for item in results:

        benchmark.append({

            "category":
                item["risk_category"],

            "vendor_score":
                item["risk_score"],

            "industry_average":
                industry_average,

            "difference":
                item["risk_score"]
                - industry_average
        })

    return benchmark