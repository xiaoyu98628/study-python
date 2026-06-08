from langchain.agents import create_agent

from day1.mcp_client import load_mcp_tools
from day1.model import build_model
from day1.skills.registry import render_skills_prompt
from day1.tools.registry import get_tools

PROMPT = """
当用户询问实时信息、新闻、价格、政策、网页内容或你不确定的信息时，优先使用联网工具。
当用户提供具体 URL 或需要阅读搜索结果中的网页内容时，调用 fetch_url；不知道 URL 时先调用 web_search。
当用户询问当前位置、当前城市、我在哪里等问题时，调用 get_current_location；该工具基于高德 IP 定位，只能返回大致位置。
当用户询问今天几号、周几、当前时间、日期换算等实时日期时间问题时，必须调用 get_current_datetime 工具，不要凭记忆猜测。
回答涉及网页资料时，附上来源链接。
不要编造来源。
"""


def build_system_prompt() -> str:
    return f"{PROMPT.strip()}\n\n{render_skills_prompt()}"


def build_agent():
    tools = [*get_tools(), *load_mcp_tools()]
    return create_agent(
        model=build_model(),
        tools=tools,
        system_prompt=build_system_prompt(),
    )
