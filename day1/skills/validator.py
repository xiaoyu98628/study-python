from pathlib import Path
from typing import Literal

from day1.skills.base import SkillValidationIssue
from day1.skills.registry import SKILLS_DIR
from paths import BASE_DIR


def _relative_path(path: Path) -> str:
    return str(path.resolve().relative_to(BASE_DIR))


def _issue(path: Path, severity: Literal["error", "warning"], message: str) -> SkillValidationIssue:
    return SkillValidationIssue(
        path=_relative_path(path),
        severity=severity,
        message=message,
    )


def _split_skill_file(path: Path) -> tuple[dict[str, str], str, list[SkillValidationIssue]]:
    issues = []
    lines = path.read_text(encoding="utf-8").splitlines()

    if not lines:
        return {}, "", [_issue(path, "error", "SKILL.md 不能为空")]

    if lines[0].strip() != "---":
        return {}, "\n".join(lines).strip(), [_issue(path, "error", "SKILL.md 必须以 YAML frontmatter 开头")]

    metadata_lines = []
    body_start = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start = index + 1
            break
        metadata_lines.append(line)

    if body_start is None:
        return {}, "", [_issue(path, "error", "SKILL.md 缺少结束 frontmatter 的 ---")]

    metadata = _parse_frontmatter(metadata_lines)
    body = "\n".join(lines[body_start:]).strip()
    return metadata, body, issues


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    metadata = {}
    for line in lines:
        if not line.strip() or line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _validate_skill_file(path: Path) -> tuple[SkillValidationIssue, ...]:
    metadata, body, issues = _split_skill_file(path)
    if any(issue.severity == "error" for issue in issues):
        return tuple(issues)

    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()

    if not name:
        issues.append(_issue(path, "error", "frontmatter 缺少字段：name"))
    if not description:
        issues.append(_issue(path, "error", "frontmatter 缺少字段：description"))
    if not body:
        issues.append(_issue(path, "error", "SKILL.md 正文不能为空"))
    if name and name != path.parent.name:
        issues.append(_issue(path, "warning", f"name 与目录名不一致：name={name!r}, directory={path.parent.name!r}"))

    return tuple(issues)


def validate_skills() -> tuple[SkillValidationIssue, ...]:
    issues = []
    skill_paths = sorted(
        path
        for path in SKILLS_DIR.glob("*/SKILL.md")
        if not path.parts[-2].startswith(".")
    )

    for path in skill_paths:
        issues.extend(_validate_skill_file(path))

    return tuple(issues)
