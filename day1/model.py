import logging
from pathlib import Path
from typing import Any

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from config.config import config
from day1.tools.fetch_url import fetch_url
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

model_config = config().model

model = init_chat_model(
    model="glm-5.1",
    model_provider="openai",
    api_key=model_config.aliyun_api_key,
    base_url=model_config.aliyun_base_url,
).bind_tools([get_weather, web_search, fetch_url, get_current_datetime])

tools: dict[str, Any] = {
    "get_weather": get_weather,
    "web_search": web_search,
    "fetch_url": fetch_url,
    "get_current_datetime": get_current_datetime,
}

prompt = """
当用户询问实时信息、新闻、价格、政策、网页内容或你不确定的信息时，优先使用联网工具。
当用户提供具体 URL 或需要阅读搜索结果中的网页内容时，调用 fetch_url；不知道 URL 时先调用 web_search。
当用户询问今天几号、周几、当前时间、日期换算等实时日期时间问题时，必须调用 get_current_datetime 工具，不要凭记忆猜测。
回答涉及网页资料时，附上来源链接。
不要编造来源。
"""

system_message = SystemMessage(content=prompt)

messages: list[HumanMessage | SystemMessage | AIMessage | ToolMessage] = [system_message]

while True:

    user_input = input("USER：")

    human_message = HumanMessage(content=user_input)

    if user_input == "exit":
        break

    messages.append(human_message)
    logger.debug("user_input=%r messages_count=%s", user_input, len(messages))

    ai_message_chunk = None


    print("AI: ", end="", flush=True)
    try:
        for chunk in model.stream(messages):

            logger.debug("final_stream_chunk %r",chunk)

            if ai_message_chunk is None:
                ai_message_chunk = chunk
            else:
                ai_message_chunk += chunk

            if chunk.content:
                print(chunk.content, end="", flush=True)
    except Exception:
        logger.exception("first_model_stream_failed")
        print()
        continue

    print()

    if ai_message_chunk is None:
        logger.warning("first_model_stream_empty")
        continue

    logger.debug("first_ai_content=%r", ai_message_chunk.content)
    logger.debug("first_ai_tool_calls=%r", ai_message_chunk.tool_calls)

    ai_message = AIMessage(
        content=ai_message_chunk.content,
        tool_calls=ai_message_chunk.tool_calls,
    )

    messages.append(ai_message)

    if not ai_message_chunk.tool_calls:
        continue

    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.debug("calling_tool name=%s args=%r", tool_name, tool_args)

        try:
            tool_result = tools[tool_name].invoke(tool_args)
            logger.debug("tool_result name=%s result=%r", tool_name, tool_result)
        except Exception:
            logger.exception("tool_call_failed name=%s args=%r", tool_name, tool_args)
            tool_result = "工具调用失败，错误已记录到日志。"

        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    final_content = ""

    try:
        for chunk in model.stream(messages):
            logger.debug("final_stream_chunk %r",chunk)

            if chunk.content:
                print(chunk.content, end="", flush=True)
                final_content += chunk.content
    except Exception:
        logger.exception("final_model_stream_failed")
        print()
        continue

    print()

    if not final_content:
        logger.warning("final_content_empty")

    messages.append(AIMessage(content=final_content))
