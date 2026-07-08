from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    tokens_used: int = 0
    latency_ms: int = 0
    model: str = ""


class LLMClient:
    """OpenAI 兼容 API 客户端 — 复用 httpx 连接池。"""

    def __init__(self) -> None:
        self.api_base = settings.LLM_API_BASE.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.default_model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(float(self.timeout)),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        if not self.enabled:
            raise RuntimeError("LLM_API_KEY 未配置，无法调用大模型")

        chosen_model = model or self.default_model
        payload = {
            "model": chosen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_base}/chat/completions"
        started = time.perf_counter()
        client = await self.ensure_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = int(usage.get("total_tokens", 0))
        return LLMResponse(content=content, tokens_used=tokens, latency_ms=latency_ms, model=chosen_model)


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def close_llm_client() -> None:
    global _llm_client
    if _llm_client is not None:
        await _llm_client.close()


async def init_llm_client() -> None:
    client = get_llm_client()
    if client.enabled:
        await client.ensure_client()
