from langchain.chat_models import init_chat_model

from config.config import config


def build_model():
    model_config = config().model
    return init_chat_model(
        model="glm-5.1",
        model_provider="openai",
        api_key=model_config.aliyun_api_key,
        base_url=model_config.aliyun_base_url,
    )
