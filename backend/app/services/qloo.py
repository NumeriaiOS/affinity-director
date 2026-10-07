from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import settings


class QlooError(RuntimeError):
    pass


def build_insights_payload(
    *,
    signal_names: list[str],
    filter_type: str,
    location: str | None = None,
    take: int = 8,
    explainability: bool = True,
) -> dict:
    names = [name.strip() for name in signal_names if name and name.strip()]
    if not names:
        raise ValueError("at least one signal name is required")
    if not filter_type.startswith("urn:entity:"):
        raise ValueError("filter_type must be a Qloo entity URN")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")

    payload: dict[str, object] = {
        "filter.type": filter_type,
        "signal.interests.entities.query": names,
        "take": take,
    }
    if location and location.strip():
        payload["filter.location.query"] = location.strip()
    if explainability:
        payload["feature.explainability"] = True
    return payload


class QlooClient:
    """Small Qloo API v2 client with explicit failure semantics."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.qloo_api_key
        self.base_url = (base_url or settings.qloo_base_url).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def insights(self, payload: dict) -> dict:
        if not self.api_key:
            raise QlooError("QLOO_API_KEY is not configured")

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/v2/insights",
            data=body,
            method="POST",
            headers={
                "x-api-key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", errors="replace")
            raise QlooError(f"Qloo HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise QlooError(f"Qloo network error: {exc.reason}") from exc

    def discover(
        self,
        *,
        signal_names: list[str],
        filter_type: str,
        location: str | None = None,
        take: int = 8,
    ) -> dict:
        payload = build_insights_payload(
            signal_names=signal_names,
            filter_type=filter_type,
            location=location,
            take=take,
        )
        return self.insights(payload)
