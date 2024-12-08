from pathlib import Path

from configs.llm import LLMConfig
from configs.log_config import LoggingConfig
from pydantic_settings import SettingsConfigDict

CONFIG_DIR = Path(__file__).parent
BACKEND_DIR = CONFIG_DIR.parent
BASE_DIR = BACKEND_DIR.parent


class QikoGraphConfig(LLMConfig, LoggingConfig):
    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file=f"{BASE_DIR}/.env",
        env_file_encoding="utf-8",
        frozen=True,
        # ignore extra attributes
        extra="ignore",
    )
