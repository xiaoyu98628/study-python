from langchain.agents import create_agent

from day1.context import render_context_prompt
from day1.mcp_client import load_mcp_tools
from day1.model import build_model
from day1.skills.registry import render_skills_prompt
from day1.tools.registry import get_tools
from paths import BASE_DIR


PROMPTS_DIR = BASE_DIR / "day1" / "prompts"


def read_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    sections = [
        read_prompt("system.md"),
        read_prompt("context.md"),
        render_context_prompt(),
        read_prompt("tools.md"),
        render_skills_prompt(),
    ]
    return "\n\n".join(section for section in sections if section.strip())


def build_agent():
    tools = [*get_tools(), *load_mcp_tools()]
    return create_agent(
        model=build_model(),
        tools=tools,
        system_prompt=build_system_prompt(),
    )
