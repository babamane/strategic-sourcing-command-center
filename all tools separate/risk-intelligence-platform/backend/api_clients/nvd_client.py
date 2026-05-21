import requests

BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def fetch_nvd_data(keyword):

    try:
        response = requests.get(BASE_URL, params={"keywordSearch": keyword}, timeout=10)

        data = response.json()

        vulnerabilities = []

        for item in data.get("vulnerabilities", [])[:5]:

            cve = item.get("cve", {})

            vulnerabilities.append(
                {
                    "id": cve.get("id"),
                    "published": cve.get("published"),
                    "severity": (
                        cve.get("metrics", {})
                        .get("cvssMetricV31", [{}])[0]
                        .get("cvssData", {})
                        .get("baseSeverity", "UNKNOWN")
                    ),
                }
            )

        return vulnerabilities

    except Exception as e:
        return {"error": str(e)}
