from pathlib import Path

from day1.skills.base import SkillMetadata
from paths import BASE_DIR


SKILLS_DIR = Path(__file__).resolve().parent


def _read_frontmatter(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as file:
        first_line = file.readline()
        if first_line.strip() != "---":
            raise RuntimeError("SKILL.md 必须以 YAML frontmatter 开头")

        metadata_lines = []
        for line in file:
            if line.strip() == "---":
                return _parse_frontmatter(metadata_lines)
            metadata_lines.append(line.rstrip("\n"))

        raise RuntimeError("SKILL.md 缺少结束 frontmatter 的 ---")


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    metadata = {}
    for line in lines:
        if not line.strip() or line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _load_skill_metadata(path: Path) -> SkillMetadata:
    metadata = _read_frontmatter(path)
    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if not name:
        raise RuntimeError(f"{path} 缺少 frontmatter 字段：name")
    if not description:
        raise RuntimeError(f"{path} 缺少 frontmatter 字段：description")

    return SkillMetadata(
        name=name,
        description=description,
        path=str(path.resolve().relative_to(BASE_DIR)),
    )


def list_skill_metadata() -> tuple[SkillMetadata, ...]:
    skill_paths = sorted(
        path
        for path in SKILLS_DIR.glob("*/SKILL.md")
        if not path.parts[-2].startswith(".")
    )
    return tuple(_load_skill_metadata(path) for path in skill_paths)


def render_skills_metadata_prompt(skills: tuple[SkillMetadata, ...] | None = None) -> str:
    available_skills = skills or list_skill_metadata()
    lines = [
        "你拥有以下 skills。每个 skill 的 description 描述了何时使用它。",
        "当用户问题匹配某个 skill 时，必须先调用 read_file 读取该 skill 的 path，再遵守 SKILL.md 正文中的指令。",
        "不要仅凭 skill metadata 执行 skill；metadata 只用于判断是否需要读取对应的 SKILL.md。",
    ]

    for skill in available_skills:
        lines.extend(
            [
                "",
                f"Skill: {skill.name}",
                f"Description: {skill.description}",
                f"Path: {skill.path}",
            ]
        )

    return "\n".join(lines)


def get_skills() -> tuple[SkillMetadata, ...]:
    return list_skill_metadata()


def render_skills_prompt(skills: tuple[SkillMetadata, ...] | None = None) -> str:
    return render_skills_metadata_prompt(skills)
