from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings import BASE_SETTINGS_CONFIG


class SandboxConfig(BaseSettings):
    model_config = SettingsConfigDict(
        **BASE_SETTINGS_CONFIG,
    )

    sandbox_provider: str = Field(default="daytona", alias="SANDBOX_PROVIDER")
    daytona_api_key: str = Field(default="", alias="DAYTONA_API_KEY")
    daytona_api_url: str = Field(default="", alias="DAYTONA_API_URL")
    daytona_target: str = Field(default="", alias="DAYTONA_TARGET")
