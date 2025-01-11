from pydantic import Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    ONE_API_KEY: str = Field(
        description="one api key",
        default="",
    )

    ONE_API_URL: str = Field(description="one api 地址", default="")

    ONE_API_MODEL: str = Field(description="one api 模型", default="glm-4-plus")

    TAVILY_API_KEY: str = Field(description="搜索模型api key", default="")
