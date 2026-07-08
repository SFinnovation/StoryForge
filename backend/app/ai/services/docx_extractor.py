"""从 .docx 提取纯文本并清理噪音。"""

from __future__ import annotations

import re
from pathlib import Path


def extract_text_from_docx(file_path: str | Path) -> str:
    from docx import Document

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"docx 文件不存在: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError(f"仅支持 .docx 文件: {path}")

    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return clean_extracted_text("\n".join(paragraphs))


def clean_extracted_text(text: str) -> str:
    """清理 PDF/wiki 转 docx 常见噪音。"""
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^【第\s*\d+\s*页", s):
            continue
        if re.match(r"^Page\s+\d+", s, re.I):
            continue
        if s.startswith("说明：本 PDF") or s.startswith("说明:本 PDF"):
            continue
        if "/wiki/" in s and len(s) < 120:
            continue
        if s.startswith("< ") and "|" in s:
            continue
        s = re.sub(r"\(/wiki/[^)]+\)", "", s)
        s = re.sub(r"\(/index\.php[^)]+\)", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            lines.append(s)
    return "\n".join(lines)
