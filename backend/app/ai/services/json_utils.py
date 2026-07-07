from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def extract_json_text(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_model(raw: str, model: type[T]) -> T:
    payload = json.loads(extract_json_text(raw))
    return model.model_validate(payload)


def dumps_context(data: Any) -> str:
    if isinstance(data, BaseModel):
        return json.dumps(data.model_dump(), ensure_ascii=False, separators=(",", ":"))
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
