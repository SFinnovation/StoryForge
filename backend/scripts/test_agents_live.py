"""AI 模块 — 各 Agent 独立实测脚本（调用真实 LLM）。

用法（PowerShell，Key 通过环境变量传入，不落盘）：
    $env:LLM_API_KEY="sk-xxxx"
    python scripts/test_agents_live.py             # 跑全部 7 个 Agent
    python scripts/test_agents_live.py opening      # 只跑指定 Agent
    python scripts/test_agents_live.py narrative critic

可选环境变量：
    LLM_MODEL（默认 deepseek-chat）、LLM_API_BASE（默认 https://api.deepseek.com/v1）
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if not os.environ.get("LLM_API_KEY"):
    print("[ERROR] 未检测到环境变量 LLM_API_KEY，请先设置后再运行。")
    print('  PowerShell:  $env:LLM_API_KEY="sk-..."; python scripts/test_agents_live.py')
    raise SystemExit(1)

from backend.app.ai import get_ai_module
from backend.app.ai.schemas import (
    ActionParseInput,
    CharacterCard,
    CheckResult,
    ModuleExtractionInput,
    NarrativeInput,
    OpeningInput,
    RulebookExtractionInput,
    SummaryInput,
)
from backend.app.ai.schemas.narrative import NarrativeOutput, StateUpdates
from backend.app.ai.services.critic_agent import CriticAgent
from backend.app.ai.services.llm_client import close_llm_client
from backend.app.core.config import settings

RESULTS: list[dict] = []

CHARACTER = CharacterCard(
    name="艾琳",
    profession="调查员",
    background="研究失踪案件的年轻侦探",
    motivation="寻找失踪学者留下的最后一份手稿",
)

RULEBOOK_SAMPLE = """
D&D 5e 玩家手册（节选）
能力检定：当角色尝试有难度的行动时，DM 设定一个难度等级（DC）。玩家掷 d20，加上相关属性调整值与（若擅长）熟练加值，结果不低于 DC 即成功。
六大属性：力量、敏捷、体质、智力、感知、魅力。属性调整值 =（属性值 - 10）/ 2 向下取整。
优势与劣势：拥有优势时掷两个 d20 取高值；处于劣势时取低值。
熟练加值：1 级角色为 +2，随等级提升。适用于擅长的技能、豁免与武器。
休息：短休至少 1 小时，可花费生命骰恢复生命值；长休 8 小时，恢复全部生命值与半数生命骰。
战斗：以先攻（d20 + 敏捷调整）决定行动顺序。攻击掷 d20 + 攻击调整对抗目标的护甲等级（AC）。
死亡豁免：生命值降至 0 时陷入昏迷，每轮掷 d20，10 或以上为成功，累计三次成功则稳定，三次失败则死亡。
""".strip()

MODULE_SAMPLE = """
追捕克仑可（Krenko's Way）模组节选
背景：拉尼卡第十区，狗头人黑帮头目克仑可控制了地精帮派，四处劫掠。玩家受波洛斯军团委托追捕克仑可。
克仑可表面上只是街头混混头目，实则暗中与外来的恶魔信徒结盟，真正目标是夺取公会封印石以召唤恶魔。这一秘密无人知晓。
场景一：第十区主街。喧闹的集市与酒馆，帮派眼线四处游荡。可通往赌场后巷与波洛斯哨站。玩家开场在此，已知联络人给的潦草地图指向赌场后巷。
场景二：赌场后巷。狭窄阴暗，通往克仑可地下据点入口。有一扇上锁的铁门，地上有鳞片痕迹。
场景三：克仑可藏身处。地下密室，狗头人与地精混杂，克仑可端坐宝座，旁边有赃物箱。
NPC：公会联络人（精灵信使，谨慎务实，知道任务与克仑可行踪传闻，但不知恶魔结盟之事）；双面间谍（持有铁门钥匙，同时向公会与克仑可卖情报）。
""".strip()


def _section(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _kv(label: str, value: str) -> None:
    print(f"{label}: {value}")


def _pretty(model) -> str:
    return json.dumps(model.model_dump(), ensure_ascii=False, indent=2)


def _record(name: str, ok: bool, tokens: int, latency: int, note: str) -> None:
    RESULTS.append({"name": name, "ok": ok, "tokens": tokens, "latency": latency, "note": note})
    flag = "[PASS]" if ok else "[FAIL]"
    print(f"\n{flag}  tokens={tokens}  latency={latency}ms  — {note}")


async def test_opening() -> None:
    _section("1. OpeningAgent — 开局剧情生成")
    ai = get_ai_module()
    _kv("输入", "world=古堡悬疑, character=艾琳/调查员")
    out = await ai.generate_opening(OpeningInput(world="古堡悬疑", character=CHARACTER))
    o = out.output
    _kv("scene_title", o.scene_title)
    _kv("main_task", o.main_task)
    print(f"narration:\n{o.narration}")
    _kv("npcs", ", ".join(n.name for n in o.npcs) or "（无）")
    _kv("initial_clues 数量", str(len(o.initial_clues)))
    ok = bool(o.scene_title) and len(o.narration) > 50
    _record("OpeningAgent", ok, out.tokens_used, out.latency_ms,
            "生成场景标题与叙事" if ok else "输出字段不完整")


async def test_action_parser() -> None:
    _section("2. ActionParserAgent — 行动解析")
    ai = get_ai_module()
    action = "我悄悄绕到大厅侧面，避开管家视线，检查那座停摆的落地钟。"
    _kv("输入行动", action)
    out = await ai.parse_action(
        ActionParseInput(player_action=action, current_scene="黑鸦古堡大厅", character=CHARACTER)
    )
    print(_pretty(out.output))
    o = out.output
    ok = bool(o.attribute_used) and 5 <= o.suggested_dc <= 30 and isinstance(o.needs_check, bool)
    _record("ActionParserAgent", ok, out.tokens_used, out.latency_ms,
            f"action_type={o.action_type}, DC={o.suggested_dc}, needs_check={o.needs_check}")


async def test_narrative() -> None:
    _section("3. NarrativeAgent + CriticAgent（RevisionLoop 全链路）")
    ai = get_ai_module()
    _kv("输入", "行动=检查落地钟, 判定=失败(d20=9<DC12), clue_pressure=0.3")
    story = await ai.generate_narrative(
        NarrativeInput(
            player_action="我悄悄检查那座停摆的落地钟，寻找隐藏机关。",
            check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12, check_type="调查"),
            current_scene="黑鸦古堡大厅",
            known_clues=["钟摆已经停止"],
            clue_pressure=0.3,
            world="古堡悬疑",
            character=CHARACTER,
            public_world_facts=["黑鸦古堡曾是失踪学者的居所"],
        ),
        hidden_truths=["落地钟背后藏有通往地下室的暗门，机关需要特定钥匙开启。"],
    )
    print(f"narration:\n{story.narrative.narration}")
    _kv("visible_result", story.narrative.visible_result)
    _kv("next_options", " | ".join(story.narrative.next_options))
    _kv("审核 approved", str(story.review.approved))
    _kv("overall_score", str(story.review.overall_score))
    _kv("revision_count", str(story.revision_count))
    _kv("used_fallback", str(story.used_fallback))
    ok = len(story.narrative.narration) > 30 and story.review.overall_score > 0
    _record("NarrativeAgent", ok, story.tokens_used, story.latency_ms,
            f"审核分={story.review.overall_score}, 修正{story.revision_count}次")


async def test_critic_standalone() -> None:
    _section("4. CriticAgent — 独立审核（故意构造违规叙事）")
    critic = CriticAgent()
    narrative_input = NarrativeInput(
        player_action="我检查那座停摆的落地钟。",
        check_result=CheckResult(success=False, dice_roll=9, final_value=11, dc=12, check_type="调查"),
        current_scene="黑鸦古堡大厅",
        world="古堡悬疑",
        character=CHARACTER,
    )
    bad_narrative = NarrativeOutput(
        narration="你一眼就发现落地钟背后有一扇通往地下室的暗门，机关轻松打开，你径直走了进去。",
        visible_result="成功找到暗门并打开。",
        state_updates=StateUpdates(),
    )
    _kv("被审叙事", bad_narrative.narration)
    _kv("规则事实", "判定失败(success=False)，叙事却写成成功并泄露暗门真相")
    review, llm = await critic.review(
        bad_narrative,
        narrative_input,
        hidden_truths=["落地钟背后藏有通往地下室的暗门，机关需要特定钥匙开启。"],
    )
    print(_pretty(review))
    tokens = llm.tokens_used if llm else 0
    latency = llm.latency_ms if llm else 0
    ok = review.approved is False
    _record("CriticAgent", ok, tokens, latency,
            "正确驳回违规叙事" if ok else "未能识别违规(approved=True)")


async def test_summary() -> None:
    _section("5. SummaryAgent — 本局总结")
    ai = get_ai_module()
    out = await ai.generate_summary(
        SummaryInput(
            world="古堡悬疑",
            character=CHARACTER,
            player_actions=["观察大厅", "检查落地钟", "询问老管家午夜钟声的秘密"],
            check_results=[
                CheckResult(success=False, dice_roll=9, final_value=11, dc=12, check_type="调查"),
                CheckResult(success=True, dice_roll=17, final_value=20, dc=15, check_type="交涉"),
            ],
            ai_narrations=["你在昏暗大厅中摸索，未能发现暗门。", "老管家含糊地提到午夜钟声后不要外出。"],
            discovered_clues=["钟摆停止", "午夜钟声的禁忌"],
        )
    )
    o = out.output
    _kv("title", o.title)
    _kv("ending_type", o.ending_type)
    print(f"story_summary:\n{o.story_summary}")
    _kv("key_choices", " | ".join(o.key_choices))
    _kv("next_suggestion", o.next_suggestion)
    ok = bool(o.title) and len(o.story_summary) > 30
    _record("SummaryAgent", ok, out.tokens_used, out.latency_ms, "生成战报总结")


async def test_rulebook() -> None:
    _section("6. RulebookExtractorAgent — 规则书提取（样例节选）")
    ai = get_ai_module()
    _kv("输入", f"D&D 5e 规则节选（{len(RULEBOOK_SAMPLE)} 字符）")
    out = await ai.extract_rulebook(
        RulebookExtractionInput(source_name="PHB样例.docx", raw_text=RULEBOOK_SAMPLE, focus="lite_dnd")
    )
    o = out.output
    _kv("title", o.title)
    _kv("world_style", o.world_style)
    print(f"world_setting:\n{o.world_setting}")
    print("public_world_facts:")
    for f in o.public_world_facts:
        print(f"  - [{f.importance}/{f.category}] {f.content}")
    print(f"core_rules_summary:\n{o.core_rules_summary}")
    ok = bool(o.world_setting) and bool(o.world_style) and len(o.public_world_facts) >= 1
    _record("RulebookExtractorAgent", ok, out.tokens_used, out.latency_ms,
            f"提取 {len(o.public_world_facts)} 条规则事实")


async def test_module() -> None:
    _section("7. ModuleExtractorAgent — 模组提取（样例节选）")
    ai = get_ai_module()
    _kv("输入", f"追捕克仑可模组节选（{len(MODULE_SAMPLE)} 字符）")
    out = await ai.extract_module(
        ModuleExtractionInput(source_name="追捕克仑可.docx", raw_text=MODULE_SAMPLE, module_title="追捕克仑可")
    )
    o = out.output
    _kv("title", o.title)
    _kv("current_scene", o.current_scene)
    print(f"story_summary:\n{o.story_summary}")
    print(f"scenes ({len(o.scenes)}):")
    for s in o.scenes:
        print(f"  - {s.scene_id} / {s.title} -> 出口: {', '.join(s.exits) or '无'}")
    print("hidden_truths:")
    for h in o.hidden_truths:
        print(f"  - {h}")
    print("visible_npcs: " + (", ".join(n.name for n in o.visible_npcs) or "（无）"))
    ok = bool(o.story_summary) and len(o.scenes) >= 1 and bool(o.current_scene)
    _record("ModuleExtractorAgent", ok, out.tokens_used, out.latency_ms,
            f"提取 {len(o.scenes)} 场景 / {len(o.hidden_truths)} 隐藏真相")


TESTS = {
    "opening": test_opening,
    "action": test_action_parser,
    "narrative": test_narrative,
    "critic": test_critic_standalone,
    "summary": test_summary,
    "rulebook": test_rulebook,
    "module": test_module,
}


async def main() -> None:
    selected = [a.lower() for a in sys.argv[1:]] or list(TESTS.keys())
    print("StoryForge AI Agent 实测")
    _kv("模型", f"{settings.LLM_MODEL} @ {settings.LLM_API_BASE}")
    _kv("待测 Agent", ", ".join(selected))

    started = time.perf_counter()
    for key in selected:
        fn = TESTS.get(key)
        if fn is None:
            print(f"未知 Agent: {key}（可选: {', '.join(TESTS)}）")
            continue
        try:
            await fn()
        except Exception as exc:  # noqa: BLE001
            _record(key, False, 0, 0, f"异常: {type(exc).__name__}: {exc}")
    await close_llm_client()

    _section("汇总")
    total_tokens = sum(r["tokens"] for r in RESULTS)
    print(f"{'Agent':<26}{'结果':<8}{'tokens':<10}{'延迟(ms)':<10}备注")
    print("-" * 78)
    for r in RESULTS:
        flag = "PASS" if r["ok"] else "FAIL"
        print(f"{r['name']:<24}{flag:<8}{r['tokens']:<10}{r['latency']:<10}{r['note']}")
    passed = sum(1 for r in RESULTS if r["ok"])
    elapsed = time.perf_counter() - started
    print("-" * 78)
    print(f"通过 {passed}/{len(RESULTS)} · 总 tokens={total_tokens} · 总耗时={elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
