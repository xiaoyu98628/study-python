from pydantic import BaseModel

from config.model import ModelConfig
from config.sandbox import SandboxConfig
from config.tool import ToolConfig


class Config(BaseModel):
    model: ModelConfig
    tool: ToolConfig
    sandbox: SandboxConfig


def config() -> Config:
    """获取配置。"""
    return Config(
        model=ModelConfig(),
        tool=ToolConfig(),
        sandbox=SandboxConfig(),
    )
