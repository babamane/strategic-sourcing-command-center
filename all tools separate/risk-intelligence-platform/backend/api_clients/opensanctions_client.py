import requests


BASE_URL = "https://api.opensanctions.org/match/sanctions"


def fetch_opensanctions_data(company_name):

    try:

        payload = {
            "queries": {
                "vendor": {"schema": "Company", "properties": {"name": [company_name]}}
            }
        }

        response = requests.post(BASE_URL, json=payload, timeout=20)

        if response.status_code != 200:

            return {
                "warning": "OpenSanctions unavailable",
                "status_code": response.status_code,
            }

        data = response.json()

        return data

    except Exception as e:

        return {"warning": "OpenSanctions timeout/unavailable", "error": str(e)}
