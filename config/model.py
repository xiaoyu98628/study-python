from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class ModelConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
    )

    zai_api_key: str = Field(default="", alias="ZAI_API_KEY", description="API Key")
    zai_base_url: str = Field(default="", alias="ZAI_BASE_URL", description="API Key")