from pydantic import BaseModel

from config.model import ModelConfig
from config.tool import ToolConfig


class Config(BaseModel):
    model: ModelConfig
    tool: ToolConfig


def config() -> Config:
    """获取配置。"""
    return Config(
        model=ModelConfig(),
        tool=ToolConfig(),
    )
