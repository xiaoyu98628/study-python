from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class ModelConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
    )

    zai_api_key: str = Field(default="", alias="ZAI_API_KEY", description="Zai API Key")
    zai_base_url: str = Field(default="", alias="ZAI_BASE_URL", description="API Base Url")

    aliyun_api_key: str = Field(default="", alias="ALIYUN_API_KEY", description="AliYun API Key")
    aliyun_base_url: str = Field(default="", alias="ALIYUN_BASE_URL", description="AliYun API Base Url")
