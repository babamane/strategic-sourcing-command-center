import requests

from config.settings import settings


def fetch_otx_data(domain):

    try:

        url = f"""
https://otx.alienvault.com
/api/v1/indicators/domain/
{domain}/general
"""

        headers = {

            "X-OTX-API-KEY":
                settings.OTX_API_KEY
        }

        response = requests.get(

            url,

            headers=headers,

            timeout=20
        )

        data = response.json()

        return {

            "pulse_count":
                data.get("pulse_info", {})
                .get("count", 0),

            "reputation":
                data.get("reputation", 0)
        }

    except Exception as e:

        return {
            "error": str(e)
        }