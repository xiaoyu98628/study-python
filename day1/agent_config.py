import argparse
import json
from pathlib import Path
from typing import Any

from paths import BASE_DIR


AGENT_CONFIG_FILE = BASE_DIR / "config" / "agent.json"


def load_agent_config(path: Path = AGENT_CONFIG_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"agent config 文件必须是 JSON object：{path}")

    return data


def validate_agent_config(agent_config: dict[str, Any]) -> list[str]:
    errors = []

    for key in ("disabled_skills", "disabled_tools"):
        if key not in agent_config:
            continue

        value = agent_config[key]
        if not isinstance(value, list):
            errors.append(f"{key} 必须是 array")
            continue

        for index, item in enumerate(value):
            if not isinstance(item, str):
                errors.append(f"{key}[{index}] 必须是 string")

    return errors


def get_disabled_skills(agent_config: dict[str, Any] | None = None) -> set[str]:
    data = load_agent_config() if agent_config is None else agent_config
    disabled_skills = data.get("disabled_skills", [])
    if not isinstance(disabled_skills, list):
        return set()

    return {skill_name for skill_name in disabled_skills if isinstance(skill_name, str)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or preview agent config.")
    parser.add_argument(
        "--path",
        type=Path,
        default=AGENT_CONFIG_FILE,
        help="Path to agent config JSON file.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the agent config JSON structure.",
    )
    args = parser.parse_args()

    agent_config = load_agent_config(args.path)

    if args.validate:
        errors = validate_agent_config(agent_config)
        if errors:
            for error in errors:
                print(f"ERROR {error}")
            raise SystemExit(1)
        print("OK")
        return

    print(json.dumps(agent_config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
