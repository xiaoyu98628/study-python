import logging
from typing import Any

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from config.config import config
from day1.tools.time_tool import get_current_datetime
from day1.tools.weather import get_weather
from day1.tools.web_tool import web_search
from paths import BASE_DIR


LOG_DIR = BASE_DIR / "storage" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "agent.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("day1.agent")

model_config = config().model

model = init_chat_model(
    model="glm-5.1",
    # model="qwen3.7-plus",
    model_provider="openai",
    api_key=model_config.zai_api_key,
    base_url=model_config.zai_base_url,
).bind_tools([get_weather, web_search, get_current_datetime])

tools: dict[str, Any] = {
    "get_weather": get_weather,
    "web_search": web_search,
    "get_current_datetime": get_current_datetime,
}

prompt = """
当用户询问实时信息、新闻、价格、政策、网页内容或你不确定的信息时，优先使用联网工具。
当用户询问今天几号、周几、当前时间、日期换算等实时日期时间问题时，必须调用 get_current_datetime 工具，不要凭记忆猜测。
回答涉及网页资料时，附上来源链接。
不要编造来源。
"""

system_message = SystemMessage(content=prompt)

messages: list[HumanMessage | SystemMessage | AIMessage | ToolMessage] = [system_message]

while True:

    user_input = input("USER：")
    logger.info("user_input=%r", user_input)

    human_message = HumanMessage(content=user_input)

    if user_input == "exit":
        logger.info("exit")
        break

    messages.append(human_message)

    ai_message_chunk = None


    print("AI: ", end="", flush=True)
    try:
        for chunk in model.stream(messages):

            logger.debug("first_stream_chunk=%r", chunk)

            if ai_message_chunk is None:
                ai_message_chunk = chunk
            else:
                ai_message_chunk += chunk

            if chunk.content:
                print(chunk.content, end="", flush=True)
    except Exception:
        logger.exception("first_model_stream_failed")
        print("模型调用失败，详情见 storage/logs/agent.log")
        continue

    print()

    if ai_message_chunk is None:
        logger.warning("first_model_stream_empty")
        print("模型没有返回内容，详情见 storage/logs/agent.log")
        continue

    logger.info(
        "first_ai_response content_len=%s tool_calls_count=%s",
        len(ai_message_chunk.content or ""),
        len(ai_message_chunk.tool_calls or []),
    )

    ai_message = AIMessage(
        content=ai_message_chunk.content,
        tool_calls=ai_message_chunk.tool_calls,
    )

    messages.append(ai_message)

    if not ai_message_chunk.tool_calls:
        if not ai_message_chunk.content:
            logger.warning("first_ai_response_empty_without_tool_calls")
        continue

    tool_failed = False

    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info("tool_call name=%s args=%r", tool_name, tool_args)

        try:
            tool_result = tools[tool_name].invoke(tool_args)
        except Exception:
            logger.exception("tool_call_failed name=%s args=%r", tool_name, tool_args)
            print(f"工具 {tool_name} 调用失败，详情见 storage/logs/agent.log")
            tool_failed = True
            break

        logger.info("tool_result name=%s result_len=%s", tool_name, len(str(tool_result)))
        logger.debug("tool_result name=%s result=%r", tool_name, tool_result)

        messages.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            )
        )

    if tool_failed:
        continue

    final_content = ""

    try:
        for chunk in model.stream(messages):
            logger.debug("final_stream_chunk=%r", chunk)
            if chunk.content:
                print(chunk.content, end="", flush=True)
                final_content += chunk.content
    except Exception:
        logger.exception("final_model_stream_failed")
        print("模型二次调用失败，详情见 storage/logs/agent.log")
        continue

    print()

    logger.info("final_ai_response content_len=%s", len(final_content))
    if not final_content:
        logger.warning("final_ai_response_empty")

    messages.append(AIMessage(content=final_content))
