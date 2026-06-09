import json
from pathlib import Path
from typing import Any

from paths import BASE_DIR


CONTEXT_FILE = BASE_DIR / "storage" / "app" / "context" / "context.json"


def load_context(path: Path = CONTEXT_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"context 文件必须是 JSON object：{path}")

    return data


def render_context_prompt(context: dict[str, Any] | None = None) -> str:
    context_data = load_context() if context is None else context
    if not context_data:
        return ""

    context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    return f"<context>\n{context_json}\n</context>"
