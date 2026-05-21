import requests
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

last_request_time = 0


session = requests.Session()

retries = Retry(total=2, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])

session.mount("https://", HTTPAdapter(max_retries=retries))


headers = {"User-Agent": "RiskIntelPlatform/1.0"}


def fetch_gdelt_data(company_name):

    global last_request_time

    try:

        # Rate limit protection
        current_time = time.time()

        elapsed = current_time - last_request_time

        if elapsed < 5:
            time.sleep(5 - elapsed)

        last_request_time = time.time()

        query = (
            f'"{company_name}" AND '
            "(strike OR protest OR disruption OR "
            "bankruptcy OR sanctions OR lawsuit OR cyberattack)"
        )

        response = session.get(
            BASE_URL,
            params={
                "query": query,
                "mode": "ArtList",
                "maxrecords": 5,
                "format": "json",
            },
            headers=headers,
            timeout=25,
        )

        if response.status_code == 429:

            return {"warning": "GDELT rate limit exceeded"}

        if response.status_code != 200:

            return {"warning": "GDELT unavailable", "status_code": response.status_code}

        data = response.json()

        articles = []

        for article in data.get("articles", []):

            articles.append(
                {
                    "title": article.get("title"),
                    "source": article.get("sourceCommonName"),
                    "url": article.get("url"),
                    "seendate": article.get("seendate"),
                }
            )

        return articles

    except Exception as e:

        return {"warning": "GDELT timeout/unavailable", "error": str(e)}
