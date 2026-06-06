from pathlib import Path

from day1.skills.base import Skill


SKILLS_DIR = Path(__file__).resolve().parent


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise RuntimeError("SKILL.md 必须以 YAML frontmatter 开头")

    metadata_lines = []
    body_start = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start = index + 1
            break
        metadata_lines.append(line)

    if body_start is None:
        raise RuntimeError("SKILL.md 缺少结束 frontmatter 的 ---")

    metadata = _parse_frontmatter(metadata_lines)
    body = "\n".join(lines[body_start:]).strip()
    return metadata, body


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    metadata = {}
    for line in lines:
        if not line.strip() or line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _read_tools(body: str) -> tuple[str, ...]:
    lines = body.splitlines()
    tools = []
    in_tools_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_tools_section = stripped == "## Tools"
            continue
        if in_tools_section and stripped.startswith("- "):
            tools.append(stripped[2:].strip())

    return tuple(tools)


def _load_skill(path: Path) -> Skill:
    metadata, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if not name:
        raise RuntimeError(f"{path} 缺少 frontmatter 字段：name")
    if not description:
        raise RuntimeError(f"{path} 缺少 frontmatter 字段：description")

    return Skill(
        name=name,
        description=description,
        body=body,
        path=str(path),
        tool_names=_read_tools(body),
    )


def get_skills() -> tuple[Skill, ...]:
    skill_paths = sorted(
        path
        for path in SKILLS_DIR.glob("*/SKILL.md")
        if not path.parts[-2].startswith(".")
    )
    return tuple(_load_skill(path) for path in skill_paths)


def render_skills_prompt(skills: tuple[Skill, ...] | None = None) -> str:
    active_skills = skills or get_skills()
    lines = [
        "你拥有以下 skills。每个 skill 的 description 描述了何时使用它；当用户问题匹配时，遵守该 skill 的正文指令："
    ]

    for skill in active_skills:
        lines.extend(
            [
                "",
                f"Skill: {skill.name}",
                f"Description: {skill.description}",
            ]
        )
        if skill.tool_names:
            lines.append(f"Tools: {', '.join(skill.tool_names)}")
        lines.extend(["Instructions:", skill.body])

    return "\n".join(lines)
