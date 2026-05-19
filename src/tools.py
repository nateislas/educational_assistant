import os

from exa_py import Exa
from langchain.tools import tool

# Initialize the Exa client
exa_client = Exa(api_key=os.environ.get("EXA_API_KEY"))


@tool
def exa_search_tool(query: str) -> str:
    """
    Search the web for real, concrete facts (specific names, dates, events, numbers, metrics) using Exa.
    Input should be an Exa-optimized declarative query.
    Returns the titles, URLs, and key highlights of the top 3 results.
    """
    try:
        response = exa_client.search_and_contents(
            query,
            num_results=3,
            text=False,
            highlights=True
        )
        
        formatted_results = []
        for i, result in enumerate(response.results):
            title = result.title or "No Title"
            url = result.url or "No URL"
            highlights = "\n".join(result.highlights) if result.highlights else "No highlights available."
            formatted_results.append(
                f"Result [{i+1}]: {title}\nURL: {url}\nHighlights:\n{highlights}\n"
            )
        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"Search failed due to API error: {e}. Proceed with best available knowledge or try a different search style."
