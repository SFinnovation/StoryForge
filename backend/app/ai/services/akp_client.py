"""AKP 客户端 — 封装 Auditable Knowledge Packs 的确定性 subprocess 调用。

设计要点（见 docs/akp-integration-plan.md §6）：
- 通过 subprocess 调用 vendored `third_party/akp`，不引入进程内耦合，便于替换/回退。
- 建包用 `build_skill.py`；检索用生成包内的 `scripts/kbtool.py bundle`
  （AKP 实际 CLI 无 `research` 子命令，`bundle` 即"search+bundle 合并为一步"，
  产出带 `## References` 的确定性证据包，检索阶段不调用任何 LLM）。
- 所有对外函数在 AKP 不可用/失败时抛出 AkpError，由调用方负责回退到纯 LLM 路径。
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# 项目根：backend/app/ai/services/akp_client.py → parents[4]
_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _utf8_env() -> dict[str, str]:
    """强制子进程使用 UTF-8 收发（AKP 输出中文 + ensure_ascii=False 的 JSON）。

    Windows 默认 code page 为 GBK，不设置会导致管道解码失败 / JSON 解析出错。
    """
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run(cmd: list[str], *, cwd: str | None, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_utf8_env(),
        timeout=timeout,
    )


class AkpError(RuntimeError):
    """AKP 调用失败（建包/检索）；调用方应捕获并回退到纯 LLM 路径。"""


@dataclass
class EvidenceItem:
    node_id: str
    title: str
    reference_path: str          # 指向 references/ 的可回跳路径
    doc_title: str = ""
    source_file: str = ""


@dataclass
class ResearchBundle:
    query: str
    bundle_md: str               # 直接可注入 prompt 的证据包（含 ## References）
    evidence: list[EvidenceItem] = field(default_factory=list)
    run_dir: str = ""
    hits: int = 0

    @property
    def verify_ok(self) -> bool:
        """bundle 命中即视为通过（确定性检索，无 verify.json 阶段）。"""
        return self.hits > 0 and bool(self.bundle_md.strip())


def is_enabled() -> bool:
    return bool(settings.AKP_ENABLED)


def _python() -> str:
    return settings.AKP_PYTHON or sys.executable


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_PROJECT_ROOT / p)


def _akp_root() -> Path:
    root = _resolve(settings.AKP_ROOT)
    build_script = root / "scripts" / "build_skill.py"
    if not build_script.is_file():
        raise AkpError(f"AKP 未正确 vendoring：缺少 {build_script}")
    return root


def _slug(text: str, *, max_len: int = 48) -> str:
    """规范化为 AKP skill-name / run-id 允许的 [a-z0-9-]。"""
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        s = "pack"
    return s[:max_len].strip("-") or "pack"


def build_pack(inputs: list[Path], skill_name: str, *, title: str = "") -> Path:
    """docx/pdf/md → knowledge pack 目录（幂等，--force 重建）。

    返回生成的 skill 包根目录（`<AKP_PACKS_DIR>/<skill_name>`）。
    """
    root = _akp_root()
    out_dir = _resolve(settings.AKP_PACKS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    skill = _slug(skill_name)

    cmd = [
        _python(),
        str(root / "scripts" / "build_skill.py"),
        "--skill-name", skill,
        "--out-dir", str(out_dir),
        "--title", title or skill_name,
        "--force",
        "--inputs", *[str(p) for p in inputs],
    ]
    logger.info("AKP build_pack: %s", " ".join(cmd))
    try:
        proc = _run(cmd, cwd=None, timeout=settings.AKP_BUILD_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise AkpError(f"AKP 建包超时（>{settings.AKP_BUILD_TIMEOUT_S}s）: {skill}") from exc
    if proc.returncode != 0:
        raise AkpError(
            f"AKP 建包失败 (rc={proc.returncode}): {(proc.stderr or proc.stdout)[-800:]}"
        )

    pack_dir = out_dir / skill
    if not (pack_dir / "kb.sqlite").is_file():
        raise AkpError(f"AKP 建包未产出 kb.sqlite: {pack_dir}")
    return pack_dir


def research(
    pack_dir: Path,
    query: str,
    *,
    run_id: str,
    require_terms: list[str] | None = None,
    preset: str | None = None,
) -> ResearchBundle:
    """对已建包执行确定性检索（kbtool bundle），返回带出处的证据包。

    - `--out` 相对 skill 根目录，写入 `runs/<run_id>.md`（AKP 安全约束：产物须在包内）。
    - 检索阶段不调用任何 LLM。
    """
    pack_dir = Path(pack_dir)
    kbtool = pack_dir / "scripts" / "kbtool.py"
    if not kbtool.is_file():
        raise AkpError(f"AKP 包缺少 kbtool.py: {kbtool}")

    out_rel = f"runs/{_slug(run_id)}.md"
    cmd = [
        _python(),
        str(kbtool),
        "bundle",
        "--query", query,
        "--preset", preset or settings.AKP_BUNDLE_PRESET,
        "--out", out_rel,
        "--timeout-ms", str(settings.AKP_RESEARCH_TIMEOUT_MS),
    ]
    for t in require_terms or []:
        cmd += ["--require-term", t]

    try:
        proc = _run(
            cmd,
            cwd=str(pack_dir),
            timeout=settings.AKP_RESEARCH_TIMEOUT_MS / 1000 + 5,
        )
    except subprocess.TimeoutExpired as exc:
        raise AkpError(f"AKP 检索超时: {query}") from exc

    # bundle 命中返回 0；无命中返回 1（stdout 仍是合法 JSON，非致命）。
    if proc.returncode not in (0, 1):
        raise AkpError(
            f"AKP 检索失败 (rc={proc.returncode}): {(proc.stderr or proc.stdout)[-800:]}"
        )

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AkpError(f"AKP 检索输出非 JSON: {proc.stdout[:400]}") from exc

    return _parse_bundle(query, pack_dir, payload)


def _parse_bundle(query: str, pack_dir: Path, payload: dict) -> ResearchBundle:
    """从 kbtool bundle 的 stdout payload + 落盘 bundle.md 组装 ResearchBundle。"""
    out_rel = str(payload.get("out") or "")
    bundle_md = ""
    if out_rel:
        bundle_path = pack_dir / out_rel
        if bundle_path.is_file():
            bundle_md = bundle_path.read_text(encoding="utf-8", errors="ignore")

    evidence: list[EvidenceItem] = []
    for node in payload.get("rendered", []) or []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id") or "")
        evidence.append(
            EvidenceItem(
                node_id=node_id,
                title=str(node.get("title") or node.get("label") or node_id),
                reference_path=_ref_for_node(bundle_md, node_id),
                doc_title=str(node.get("doc_title") or ""),
                source_file=str(node.get("source_file") or ""),
            )
        )

    hits = len(payload.get("hits", []) or [])
    return ResearchBundle(
        query=query,
        bundle_md=bundle_md,
        evidence=evidence,
        run_dir=out_rel,
        hits=hits,
    )


_REF_LINE = re.compile(r"`(references/[^`]+)`")


def _ref_for_node(bundle_md: str, node_id: str) -> str:
    """从 bundle.md 中定位某节点对应的 references/ 路径（尽力而为）。"""
    if not bundle_md or not node_id:
        return ""
    lines = bundle_md.splitlines()
    for i, line in enumerate(lines):
        if node_id in line:
            for follow in lines[i : i + 6]:
                m = _REF_LINE.search(follow)
                if m:
                    return m.group(1)
    m = _REF_LINE.search(bundle_md)
    return m.group(1) if m else ""
