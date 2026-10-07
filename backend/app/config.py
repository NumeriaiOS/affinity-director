from dataclasses import dataclass, field
import os


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    qloo_api_key: str = field(default_factory=lambda: os.getenv("QLOO_API_KEY", ""))
    qloo_base_url: str = field(default_factory=lambda: os.getenv("QLOO_BASE_URL", "https://hackathon.api.qloo.com").rstrip("/"))
    qloo_live_enabled: bool = field(default_factory=lambda: env_bool("QLOO_LIVE_ENABLED", False))

    @property
    def qloo_configured(self) -> bool:
        return bool(self.qloo_api_key.strip())

    @property
    def qloo_live_ready(self) -> bool:
        return self.qloo_configured and self.qloo_live_enabled


settings = Settings()
