import requests


def fetch_gdelt_events(
    company_name
):

    try:

        query = f"""

        "{company_name}"

        protest OR strike OR
        disruption OR sanctions
        """

        url = (
            "https://api.gdeltproject.org"
            "/api/v2/doc/doc"
        )

        params = {

            "query":
                query,

            "mode":
                "ArtList",

            "maxrecords":
                5,

            "format":
                "json"
        }

        response = requests.get(

            url,

            params=params,

            timeout=20
        )

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }