import requests
import socket

from config.settings import settings

BASE_URL = "https://api.shodan.io/shodan/host"


def fetch_shodan_data(domain):

    try:

        ip = socket.gethostbyname(domain)

        url = f"{BASE_URL}/{ip}"

        response = requests.get(
            url, params={"key": settings.SHODAN_API_KEY}, timeout=20
        )

        data = response.json()

        findings = []

        for item in data.get("data", []):

            findings.append(
                {
                    "ip": ip,
                    "port": item.get("port"),
                    "service": item.get("product", "Unknown"),
                    "organization": data.get("org"),
                }
            )

        return findings

    except Exception as e:

        return {"error": str(e)}
