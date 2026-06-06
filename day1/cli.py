import logging
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from day1.agent import build_agent

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "storage" / "logs"
LOG_FILE = LOG_DIR / "app.log"
TOOL_LOG_FILE = LOG_DIR / "tool.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)
tool_logger = logging.getLogger("day1.tool")
tool_logger.setLevel(logging.DEBUG)
tool_logger.propagate = False
tool_handler = logging.FileHandler(TOOL_LOG_FILE, encoding="utf-8")
tool_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s"))
tool_logger.addHandler(tool_handler)


def _tool_calls(message: object) -> list[dict]:
    tool_calls = getattr(message, "tool_calls", None)
    if isinstance(tool_calls, list):
        return tool_calls
    return []


def _log_tool_call(call: dict) -> None:
    tool_logger.debug(
        "tool_call name=%r args=%r id=%r",
        call.get("name"),
        call.get("args"),
        call.get("id"),
    )


def _log_tool_result(message: object) -> None:
    tool_name = getattr(message, "name", None)
    tool_call_id = getattr(message, "tool_call_id", None)
    content = _content_text(getattr(message, "content", ""))
    tool_logger.debug(
        "tool_result name=%r tool_call_id=%r content_preview=%r",
        tool_name,
        tool_call_id,
        content[:1000],
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
    printed_section = False
    current_section = None

    def print_section(section: str, content: str) -> None:
        nonlocal printed_section, current_section
        if section != current_section:
            if printed_section:
                print()
            print(f"\n--- {section} ---")
            printed_section = True
            current_section = section
        print(content, end="", flush=True)

    def finish_section() -> None:
        nonlocal current_section
        if current_section is not None:
            print()
            current_section = None

    for mode, data in agent.stream(
        {"messages": messages},
        config={"recursion_limit": 10},
        stream_mode=["messages", "values"],
    ):
        if mode == "messages":
            token, metadata = data
            node = metadata.get("langgraph_node")
            logger.debug("agent_stream_token metadata=%r token=%r", metadata, token)
            for call in _tool_calls(token):
                _log_tool_call(call)
            content = _content_text(getattr(token, "content", ""))

            if node == "model":
                if content:
                    print_section("assistant", content)
            elif node == "tools":
                finish_section()
                _log_tool_result(token)
                if content:
                    print_section(f"tool:{getattr(token, 'name', 'unknown')}", content)
            elif content:
                finish_section()
                print_section(node or "message", content)
        elif mode == "values":
            finish_section()
            final_state = data
            logger.debug("agent_stream_state keys=%r", list(data.keys()))

    finish_section()

    if final_state is None:
        raise RuntimeError("agent stream 没有返回最终状态")

    final_messages = final_state["messages"]
    ai_messages = [message for message in final_messages if isinstance(message, AIMessage)]
    if not ai_messages:
        raise RuntimeError("agent stream 没有返回 AIMessage")

    final_content = _message_text(ai_messages[-1])
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
            agent = build_agent()

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
