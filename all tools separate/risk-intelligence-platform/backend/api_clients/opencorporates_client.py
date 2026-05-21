import requests


BASE_URL = "https://api.opencorporates.com/v0.4/companies/search"


def fetch_opencorporates_data(company_name):

    try:

        response = requests.get(BASE_URL, params={"q": company_name}, timeout=20)

        if response.status_code != 200:

            return {
                "warning": "OpenCorporates unavailable",
                "status_code": response.status_code,
            }

        data = response.json()

        companies = []

        results = data.get("results", {}).get("companies", [])

        for item in results[:5]:

            company = item.get("company", {})

            companies.append(
                {
                    "name": company.get("name"),
                    "jurisdiction": company.get("jurisdiction_code"),
                    "company_number": company.get("company_number"),
                    "current_status": company.get("current_status"),
                }
            )

        return companies

    except Exception as e:

        return {"warning": "OpenCorporates timeout/unavailable", "error": str(e)}
