from langchain.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient

from config.config import config


class WebSearchInput(BaseModel):
    query: str = Field(description="需要联网搜索的问题")
    max_results: int = Field(default=5, ge=1, le=10)


@tool(args_schema=WebSearchInput)
def web_search(query: str, max_results: int = 5) -> str:
    """搜索互联网，适合查询最新信息、新闻、价格、政策、网页资料等。"""
    api_key = config().tool.tavily_api_key
    if not api_key:
        raise RuntimeError("缺少环境变量 TAVILY_API_KEY")

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
    )

    results = response.get("results", [])
    if not results:
        return "没有搜索到相关结果。"

    lines = []
    for i, item in enumerate(results, start=1):
        title = item.get("title", "")
        url = item.get("url", "")
        content = item.get("content", "")
        lines.append(f"{i}. {title}\nURL: {url}\n摘要: {content}")

    return "\n\n".join(lines)