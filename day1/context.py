import argparse
import json
from pathlib import Path
from typing import Any

from paths import BASE_DIR


CONTEXT_FILE = BASE_DIR / "storage" / "app" / "context" / "context.json"


def _is_dict(value: object) -> bool:
    return isinstance(value, dict)


def load_context(path: Path = CONTEXT_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"context 文件必须是 JSON object：{path}")

    return data


def validate_context(context: dict[str, Any]) -> list[str]:
    errors = []

    user_profile = context.get("user_profile", {})
    if not _is_dict(user_profile):
        errors.append("user_profile 必须是 object")
    elif "language" in user_profile and not isinstance(user_profile["language"], str):
        errors.append("user_profile.language 必须是 string")

    response_preferences = context.get("response_preferences", {})
    if not _is_dict(response_preferences):
        errors.append("response_preferences 必须是 object")
    else:
        if "style" in response_preferences and not isinstance(response_preferences["style"], str):
            errors.append("response_preferences.style 必须是 string")
        if "depth" in response_preferences and not isinstance(response_preferences["depth"], str):
            errors.append("response_preferences.depth 必须是 string")
        if "ask_before_code_changes" in response_preferences and not isinstance(
            response_preferences["ask_before_code_changes"],
            bool,
        ):
            errors.append("response_preferences.ask_before_code_changes 必须是 boolean")

    project_context = context.get("project_context", {})
    if not _is_dict(project_context):
        errors.append("project_context 必须是 object")
    else:
        for key in ("name", "summary", "entrypoint", "agent_file", "prompt_dir", "context_file", "skills_dir", "tools_dir"):
            if key in project_context and not isinstance(project_context[key], str):
                errors.append(f"project_context.{key} 必须是 string")
        for key in ("has_tools", "has_skills", "has_sandbox"):
            if key in project_context and not isinstance(project_context[key], bool):
                errors.append(f"project_context.{key} 必须是 boolean")

    return errors


def render_context_prompt(context: dict[str, Any] | None = None) -> str:
    context_data = load_context() if context is None else context
    if not context_data:
        return ""

    context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
    return f"<context>\n{context_json}\n</context>"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or preview agent context.")
    parser.add_argument(
        "--path",
        type=Path,
        default=CONTEXT_FILE,
        help="Path to context JSON file.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the context JSON structure.",
    )
    args = parser.parse_args()

    context = load_context(args.path)

    if args.validate:
        errors = validate_context(context)
        if errors:
            for error in errors:
                print(f"ERROR {error}")
            raise SystemExit(1)
        print("OK")
        return

    print(render_context_prompt(context))


if __name__ == "__main__":
    main()
