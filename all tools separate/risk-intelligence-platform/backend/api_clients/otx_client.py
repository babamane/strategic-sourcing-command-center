import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings


BASE_URL = "https://otx.alienvault.com/api/v1/indicators/domain"


session = requests.Session()

retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

session.mount("https://", HTTPAdapter(max_retries=retries))


headers = {"X-OTX-API-KEY": settings.OTX_API_KEY, "User-Agent": "RiskIntelPlatform/1.0"}


def fetch_otx_data(domain):

    try:

        url = f"{BASE_URL}/{domain}/general"

        response = session.get(url, headers=headers, timeout=30)

        if response.status_code != 200:

            return {
                "warning": "OTX API unavailable",
                "status_code": response.status_code,
            }

        data = response.json()

        return {
            "pulse_count": data.get("pulse_info", {}).get("count", 0),
            "reputation": data.get("reputation", 0),
        }

    except Exception as e:

        return {"warning": "OTX timeout/unavailable", "error": str(e)}
