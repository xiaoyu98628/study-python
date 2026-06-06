from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: str
    tool_names: tuple[str, ...] = field(default_factory=tuple)
