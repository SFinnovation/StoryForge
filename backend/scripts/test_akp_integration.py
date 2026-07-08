"""AKP 集成冒烟测试（离线，无需 LLM API Key）。

覆盖 docs/akp-integration-plan.md P0 里程碑 M1：
1. AKP 关闭时：_build_evidence_bundles 短路返回 ([], None)，行为与现状一致。
2. AKP 开启时：build_pack + research(bundle) 跑通，产出带 ## References 的证据包。

用法：
    python backend/scripts/test_akp_integration.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ai.services import akp_client  # noqa: E402
from backend.app.core.config import settings  # noqa: E402
from backend.app.services.content_ingestion_service import (  # noqa: E402
    RULEBOOK_QUESTION_SET,
    _build_evidence_bundles,
)

SAMPLE_MD = """# 属性检定

进行属性检定时，掷 d20 加上属性调整值与熟练加值，若结果不低于难度等级(DC)则成功。

## 优势与劣势

拥有优势时掷两次骰取较高值，劣势时掷两次取较低值。

## 休息

短休可花费生命骰恢复生命值；长休可恢复大部分生命值与资源。

## 死亡豁免

生命值降至 0 时进行死亡豁免：三次成功则稳定，三次失败则死亡。
"""


def _hr(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_disabled_path() -> bool:
    _hr("① AKP 关闭 → 应短路回退（不建包）")
    settings.AKP_ENABLED = False
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "rules.md"
        f.write_text(SAMPLE_MD, encoding="utf-8")
        bundles, pack_dir = _build_evidence_bundles(
            f, RULEBOOK_QUESTION_SET, skill_name="disabled-test"
        )
    ok = bundles == [] and pack_dir is None
    print(f"bundles={len(bundles)} pack_dir={pack_dir} → {'PASS' if ok else 'FAIL'}")
    return ok


def test_enabled_path() -> bool:
    _hr("② AKP 开启 → 建包 + 逐题检索，产出带出处证据包")
    settings.AKP_ENABLED = True
    with tempfile.TemporaryDirectory() as tmp:
        settings.AKP_PACKS_DIR = str(Path(tmp) / "packs")
        f = Path(tmp) / "phb-lite.md"
        f.write_text(SAMPLE_MD, encoding="utf-8")

        pack_dir = akp_client.build_pack([f], "smoke-rulebook", title="PHB Lite")
        print(f"建包完成: {pack_dir}")
        assert (pack_dir / "kb.sqlite").is_file(), "缺少 kb.sqlite"

        bundle = akp_client.research(pack_dir, "属性检定如何计算？", run_id="q1")
        print(f"检索命中 hits={bundle.hits} verify_ok={bundle.verify_ok}")
        print(f"证据条目 evidence={len(bundle.evidence)}")
        if bundle.evidence:
            e = bundle.evidence[0]
            print(f"  首条: node_id={e.node_id!r} ref={e.reference_path!r}")
        print("---- bundle.md 预览 ----")
        print("\n".join(bundle.bundle_md.splitlines()[:12]))

        has_refs = "## References" in bundle.bundle_md
        ok = bundle.verify_ok and has_refs and len(bundle.evidence) >= 1
        print(f"\n带 ## References={has_refs} → {'PASS' if ok else 'FAIL'}")
        return ok


def main() -> int:
    results: list[tuple[str, bool]] = []
    results.append(("disabled_path", test_disabled_path()))
    try:
        results.append(("enabled_path", test_enabled_path()))
    except Exception as exc:  # noqa: BLE001
        print(f"enabled_path 异常: {type(exc).__name__}: {exc}")
        results.append(("enabled_path", False))

    _hr("汇总")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {name:<16} {'PASS' if ok else 'FAIL'}")
    print(f"\n通过 {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
