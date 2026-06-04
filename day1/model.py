from typing import Any

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from config.config import config
from day1.tool import get_weather

model_config = config().model

model = init_chat_model(
    model="glm-5.1",
    model_provider="openai",
    api_key=model_config.zai_api_key,
    base_url=model_config.zai_base_url,
).bind_tools([get_weather])

tools: dict[str, Any] = {
    "get_weather": get_weather
}

system_message = SystemMessage(content="你是AI只能助手，你叫小智.")

messages: list[HumanMessage | SystemMessage | AIMessage | ToolMessage] = [system_message]

while True:

    user_input = input("USER：")

    human_message = HumanMessage(content=user_input)

    if user_input == "exit":
        break

    messages.append(human_message)

    ai_message_chunk = None


    print("AI: ", end="", flush=True)
    for chunk in model.stream(messages):

        if ai_message_chunk is None:
            ai_message_chunk = chunk
        else:
            ai_message_chunk += chunk

        if chunk.content:
            print(chunk.content, end="", flush=True)

    print()


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

        tool_result = tools[tool_name].invoke(tool_args)

        messages.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            )
        )

    final_content = ""

    for chunk in model.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            final_content += chunk.content

    print()

    messages.append(AIMessage(content=final_content))