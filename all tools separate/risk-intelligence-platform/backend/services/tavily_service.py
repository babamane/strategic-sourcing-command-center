from tavily import TavilyClient

from config.settings import settings


client = TavilyClient(
    api_key=settings.TAVILY_API_KEY
)


def tavily_search(query):

    try:

        response = client.search(

            query=query,

            search_depth="advanced",

            max_results=10,

            include_answer=True,

            include_raw_content=True,

            timeout=15
        )

        return response

    except Exception as e:

        return {
            "error": str(e)
        }