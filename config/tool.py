from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class ToolConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
    )

    qweather_api_host: str = Field(default="", alias="QWEATHER_API_HOST", description="API Key")
    qweather_token: str = Field(default="", alias="QWEATHER_TOKEN", description="API Key")