"""长文本分块 — 供规则书 map-reduce 提取。"""

from __future__ import annotations

import re


def chunk_text(
    text: str,
    *,
    chunk_size: int = 6000,
    overlap: int = 200,
) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind("\n", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


# 规则书关键章节关键词（中英）
RULEBOOK_SECTION_KEYWORDS = [
    "属性", "检定", "技能", "熟练", "优势", "劣势", "休息", "死亡豁免",
    "战斗", "先攻", "攻击", "伤害", "豁免", "法术", "职业", "种族",
    "ability", "check", "skill", "combat", "rest", "saving throw",
]


def select_rulebook_sections(text: str, *, max_chars: int = 36000) -> str:
    """从超长规则书中筛选与跑团相关的段落，减少 LLM 输入量。"""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    scored: list[tuple[int, str]] = []
    for para in paragraphs:
        if len(para) < 20:
            continue
        score = sum(1 for kw in RULEBOOK_SECTION_KEYWORDS if kw.lower() in para.lower())
        if score > 0:
            scored.append((score, para))

    if not scored:
        return text[:max_chars]

    scored.sort(key=lambda x: x[0], reverse=True)
    selected: list[str] = []
    total = 0
    for _, para in scored:
        if total + len(para) > max_chars:
            break
        selected.append(para)
        total += len(para)

    if not selected:
        return text[:max_chars]
    return "\n".join(selected)


def truncate_for_llm(text: str, max_chars: int = 18000) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 80] + "\n\n[... 文本已截断，请基于可见部分提取 ...]"
