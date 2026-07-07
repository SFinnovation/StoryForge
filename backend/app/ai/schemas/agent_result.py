from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class AgentResult(BaseModel, Generic[T]):
    """Agent 统一返回包装 — 含业务输出与性能指标。"""

    output: T
    tokens_used: int = 0
    latency_ms: int = 0
