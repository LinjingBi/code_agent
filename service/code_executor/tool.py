from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)

def search(query: str, max_results: int = 5) -> list:
    """Search DuckDuckGo for a query.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        List of search results, each containing:
        - title: The title of the result
        - link: The URL of the result
        - snippet: A brief description of the result
    """
    ddgs = DDGS()
    results = list(ddgs.text(query, max_results=max_results))
    return results
