import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
import httpx
import json
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VoiceRoleChat"

    MAX_REQUESTS_PER_MINUTE: int = 5000
    MAX_TOKENS_PER_MINUTE: int = 800000
    TOKEN_ENCODING_NAME: str = "utf-8"
    LOGGING_LEVEL: int = 20  # INFO

    LOCAL_HOST: str = os.getenv("LOCAL_HOST","127.0.0.1")
    IS_USE_PROXY: bool = os.getenv("IS_USE_PROXY", "yes").lower() == "yes"

    IS_LOCAL_DB: bool = os.getenv("IS_LOCAL_DB") == "no"
    REDIS_HOST: Optional[str] = None if IS_LOCAL_DB else os.getenv("REDIS_HOST")
    REDIS_PORT: Optional[int] = None if IS_LOCAL_DB else int(os.getenv("REDIS_PORT", 0))
    REDIS_PWD: Optional[str] = None if IS_LOCAL_DB else os.getenv("REDIS_PWD")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", 5))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", 30))

    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 0))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")
    DATABASE_URL: str = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

    DB_ECHO: bool = False
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 10))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", 30))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", 1800))

    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", 0))
    MILVUS_URI: str = f"http://{MILVUS_HOST}:{MILVUS_PORT}"
    MILVUS_MAX_WORKERS: int = int(os.getenv("MILVUS_MAX_WORKERS", 50))

    LOCAL_PROXY_TYPE: str = os.getenv("LOCAL_PROXY_TYPE", "socks5")
    LOCAL_PROXY_PORT: int = int(os.getenv("LOCAL_PROXY_PORT", 8080))

    PROXY_URL: Optional[str] = f"{LOCAL_PROXY_TYPE}://127.0.0.1:{LOCAL_PROXY_PORT}"

    ASYNC_PROXY_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
    ASYNC_HTTP_CLIENT: Optional[httpx.AsyncClient] = None
    PROXY_HTTP_CLIENT: Optional[httpx.Client] = None
    HTTP_CLIENT: Optional[httpx.Client] = None

    OPENAI_APIKEY: str = os.getenv("OPENAI_APIKEY", "")
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "")
    TTS_URL: str = os.getenv("TTS_URL", "")
    CRYPTO_AGENT_BASEURL: str = os.getenv("CRYPTO_AGENT_BASEURL", "http://13.212.37.80:8000")

    # TTS相关配置
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SERVICE_REGION: str = os.getenv("AZURE_SERVICE_REGION", "")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._set_proxy_url()
        self._init_clients()

    def _set_proxy_url(self):
        if self.LOCAL_PROXY_TYPE and self.LOCAL_PROXY_PORT:
            self.PROXY_URL = f"{self.LOCAL_PROXY_TYPE}://127.0.0.1:{self.LOCAL_PROXY_PORT}"
        else:
            self.PROXY_URL = None

    def _init_clients(self):
        if self.PROXY_URL:
            self.ASYNC_PROXY_HTTP_CLIENT = httpx.AsyncClient(proxy=self.PROXY_URL, timeout=30)
            self.PROXY_HTTP_CLIENT = httpx.Client(proxy=self.PROXY_URL, timeout=30)
        else:
            self.ASYNC_PROXY_HTTP_CLIENT = None
            self.PROXY_HTTP_CLIENT = None

        self.ASYNC_HTTP_CLIENT = httpx.AsyncClient(timeout=30)
        self.HTTP_CLIENT = httpx.Client(timeout=30)


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()