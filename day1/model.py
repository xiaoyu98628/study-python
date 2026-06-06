import logging
from pathlib import Path

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from config.config import config
from day1.tools.fetch_url import fetch_url
from day1.tools.location import get_current_location
from day1.tools.time_tool import get_current_datetime
from day1.tools.weather import get_weather
from day1.tools.web_tool import web_search

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "storage" / "logs"
LOG_FILE = LOG_DIR / "app.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

TOOLS = [get_weather, web_search, fetch_url, get_current_location, get_current_datetime]

PROMPT = """
当用户询问实时信息、新闻、价格、政策、网页内容或你不确定的信息时，优先使用联网工具。
当用户提供具体 URL 或需要阅读搜索结果中的网页内容时，调用 fetch_url；不知道 URL 时先调用 web_search。
当用户询问当前位置、当前城市、我在哪里等问题时，调用 get_current_location；该工具基于高德 IP 定位，只能返回大致位置。
当用户询问今天几号、周几、当前时间、日期换算等实时日期时间问题时，必须调用 get_current_datetime 工具，不要凭记忆猜测。
回答涉及网页资料时，附上来源链接。
不要编造来源。
"""


def _build_agent():
    model_config = config().model
    model = init_chat_model(
        model="glm-5.1",
        model_provider="openai",
        api_key=model_config.aliyun_api_key,
        base_url=model_config.aliyun_base_url,
    )
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=PROMPT,
    )


def _message_text(message: AIMessage) -> str:
    return _content_text(message.content)


def _content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


def _stream_agent_response(agent, messages: list[BaseMessage]) -> list[BaseMessage]:
    final_state = None
    streamed_content = ""

    for mode, data in agent.stream(
        {"messages": messages},
        config={"recursion_limit": 10},
        stream_mode=["messages", "values"],
    ):
        if mode == "messages":
            token, metadata = data
            logger.debug("agent_stream_token metadata=%r token=%r", metadata, token)
            content = _content_text(getattr(token, "content", ""))
            if content:
                print(content, end="", flush=True)
                streamed_content += content
        elif mode == "values":
            final_state = data
            logger.debug("agent_stream_state keys=%r", list(data.keys()))

    if final_state is None:
        raise RuntimeError("agent stream 没有返回最终状态")

    final_messages = final_state["messages"]
    ai_messages = [message for message in final_messages if isinstance(message, AIMessage)]
    if not ai_messages:
        raise RuntimeError("agent stream 没有返回 AIMessage")

    final_content = _message_text(ai_messages[-1])
    if not streamed_content and final_content:
        print(final_content, end="", flush=True)

    logger.debug(
        "final_ai_content=%r messages_count=%s",
        final_content,
        len(final_messages),
    )
    return final_messages


def main() -> None:
    agent = None
    messages: list[BaseMessage] = []

    while True:
        user_input = input("USER：")
        if user_input == "exit":
            break

        if agent is None:
            agent = _build_agent()

        messages.append(HumanMessage(content=user_input))
        logger.debug("user_input=%r messages_count=%s", user_input, len(messages))

        print("AI: ", end="", flush=True)
        try:
            messages = _stream_agent_response(agent, messages)
        except Exception:
            logger.exception("agent_stream_failed")
            print()
            continue

        print()


if __name__ == "__main__":
    main()
