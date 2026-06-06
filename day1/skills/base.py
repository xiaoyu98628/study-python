from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    when_to_use: str
    instructions: tuple[str, ...]
    tool_names: tuple[str, ...] = field(default_factory=tuple)
