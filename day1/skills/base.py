from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: str


@dataclass(frozen=True)
class SkillValidationIssue:
    path: str
    severity: Literal["error", "warning"]
    message: str
