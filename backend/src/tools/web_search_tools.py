from langchain_core.tools import tool
from ddgs import DDGS

@tool
def web_search(query: str) -> str:
    """Search the web for up-to-date information, external medical guidelines, or general facts."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No web results found."
            return "\n\n".join(
                [f"Title: {r.get('title')}\nSnippet: {r.get('body')}" for r in results]
            )
    except Exception as e:
        return f"Error conducting web search: {str(e)}"