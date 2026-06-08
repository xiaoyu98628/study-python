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
    docker_image: str = Field(default="python:3.13-slim", alias="DOCKER_SANDBOX_IMAGE")
    docker_network: str = Field(default="none", alias="DOCKER_SANDBOX_NETWORK")
    docker_memory: str = Field(default="512m", alias="DOCKER_SANDBOX_MEMORY")
    docker_cpus: str = Field(default="1.0", alias="DOCKER_SANDBOX_CPUS")
    docker_container_prefix: str = Field(default="day1-sbx-", alias="DOCKER_SANDBOX_CONTAINER_PREFIX")
