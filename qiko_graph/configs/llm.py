from pydantic import Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    LLM_API_KEY: str = Field(
        description="大模型api key",
        default="",
    )

    TAVILY_API_KEY: str = Field(description="搜索模型api key", default="")
