from dataclasses import dataclass


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: str
