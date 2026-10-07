from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    qloo_api_key: str = os.getenv("QLOO_API_KEY", "")
    qloo_base_url: str = os.getenv("QLOO_BASE_URL", "https://api.qloo.com").rstrip("/")


settings = Settings()
