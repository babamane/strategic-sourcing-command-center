import requests

from config.settings import settings


def fetch_nvd_vulnerabilities(
    company_name
):

    try:

        url = (
            "https://services.nvd.nist.gov"
            "/rest/json/cves/2.0"
        )

        headers = {

            "apiKey":
                settings.NVD_API_KEY
        }

        params = {

            "keywordSearch":
                company_name,

            "resultsPerPage":
                5
        }

        response = requests.get(

            url,

            headers=headers,

            params=params,

            timeout=20
        )

        data = response.json()

        vulnerabilities = []

        for item in data.get(
            "vulnerabilities",
            []
        ):

            cve = item.get("cve", {})

            metrics = cve.get(
                "metrics",
                {}
            )

            severity = "UNKNOWN"
            if "cvssMetricV31" in metrics and len(metrics["cvssMetricV31"]) > 0:
                m = metrics["cvssMetricV31"][0]
                severity = m.get("cvssData", {}).get("baseSeverity") or m.get("baseSeverity") or "UNKNOWN"
            if severity == "UNKNOWN" and "cvssMetricV30" in metrics and len(metrics["cvssMetricV30"]) > 0:
                m = metrics["cvssMetricV30"][0]
                severity = m.get("cvssData", {}).get("baseSeverity") or m.get("baseSeverity") or "UNKNOWN"
            if severity == "UNKNOWN" and "cvssMetricV2" in metrics and len(metrics["cvssMetricV2"]) > 0:
                m = metrics["cvssMetricV2"][0]
                severity = m.get("baseSeverity") or m.get("cvssData", {}).get("baseSeverity") or "UNKNOWN"

            vulnerabilities.append({

                "id":
                    cve.get("id"),

                "published":
                    cve.get("published"),

                "severity":
                    severity
            })

        return vulnerabilities

    except Exception as e:

        return {
            "error": str(e)
        }