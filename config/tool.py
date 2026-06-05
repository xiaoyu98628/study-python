from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class ToolConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
    )

    qweather_private_key_path: str = Field(default="", alias="QWEATHER_PRIVATE_KEY_PATH", description="Private Key Path")
    qweather_public_key_path: str = Field(default="", alias="QWEATHER_PUBLIC_KEY_PATH", description="Public Key Path")
    qweather_api_host: str = Field(default="", alias="QWEATHER_API_HOST", description="API Key")
    qweather_project_id: str = Field(default="", alias="QWEATHER_PROJECT_ID", description="Project ID")
    qweather_key_id: str = Field(default="", alias="QWEATHER_KEY_ID", description="Project ID")