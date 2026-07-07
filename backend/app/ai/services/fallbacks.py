"""无 LLM API Key 时的演示/mock 响应，便于本地联调。"""

from app.ai.schemas.action_parse import ActionParseInput, ActionParseOutput
from app.ai.schemas.critic import CriticOutput, CriticScores
from app.ai.schemas.narrative import NarrativeInput, NarrativeOutput, StateUpdates
from app.ai.schemas.opening import OpeningInput, OpeningNpc, OpeningOutput
from app.ai.schemas.summary import SummaryInput, SummaryOutput


def mock_opening(data: OpeningInput) -> OpeningOutput:
    char = data.character
    world_name = data.resolved_world().name
    return OpeningOutput(
        scene_title="黑鸦古堡大厅",
        narration=(
            f"夜色降临，{char.name}抵达黑鸦古堡。古堡外墙爬满枯藤，铁门半开，仿佛有人刚刚离开。"
            f"你手中握着失踪学者留下的信件，信中只有一句话：“不要相信钟声之后出现的人。”\n"
            f"你现在站在古堡大厅入口。大厅里有三处值得注意的地方：\n"
            f"1. 墙上的巨大钟摆已经停止。\n"
            f"2. 东侧走廊传来微弱冷风。\n"
            f"3. 一位年迈管家站在楼梯口，似乎正在等你。"
        ),
        main_task=char.motivation or "调查古堡中的异常与失踪学者",
        npcs=[
            OpeningNpc(npc_id="butler_001", name="老管家", description="神情谨慎，似乎在等待客人")
        ],
    )


def mock_action_parse(data: ActionParseInput) -> ActionParseOutput:
    text = data.player_action
    if any(k in text for k in ("观察", "调查", "看看", "检查", "寻找线索")):
        return ActionParseOutput(
            action_type="investigate",
            skill_key="prc",
            check_type="观察",
            attribute_used="wisdom",
            suggested_dc=12,
            needs_check=True,
            intent="观察大厅环境寻找异常",
            reason="玩家正在观察大厅环境，适合使用感知属性进行检定。",
        )
    if any(k in text for k in ("潜行", "偷偷", "隐蔽")):
        return ActionParseOutput(
            action_type="stealth",
            skill_key="ste",
            check_type="潜行",
            attribute_used="dexterity",
            suggested_dc=14,
            needs_check=True,
            reason="玩家试图隐蔽行动。",
        )
    return ActionParseOutput(
        action_type="talk",
        check_type="对话",
        attribute_used="charisma",
        suggested_dc=10,
        needs_check=False,
        reason="玩家进行一般性对话或描述性行动。",
    )


def mock_narrative(data: NarrativeInput) -> NarrativeOutput:
    check = data.check_result
    if check and not check.success:
        return NarrativeOutput(
            narration=(
                "你举起手电扫过大厅，灰尘在光束中缓缓漂浮。你注意到墙上的钟摆确实停了，"
                "但由于大厅光线太暗，你没能发现更多细节。\n"
                "就在你准备靠近钟摆时，楼梯口的老管家轻声开口：“客人，夜晚最好不要碰那座钟。”"
            ),
            visible_result="观察失败，仅获得氛围信息与 NPC 警告。",
            next_options=["询问管家关于钟声的事", "转向东侧走廊", "再次尝试观察钟摆"],
        )
    return NarrativeOutput(
        narration="你的行动产生了明显效果，环境中的细节逐渐清晰起来。",
        visible_result="行动成功。",
        next_options=["继续调查", "与 NPC 对话", "前往下一区域"],
    )


def mock_critic_approve() -> CriticOutput:
    return CriticOutput(
        approved=True,
        overall_score=88,
        scores=CriticScores(
            rule_consistency=95,
            world_consistency=90,
            context_continuity=85,
            character_alignment=80,
            npc_knowledge_boundary=90,
            clue_progression=85,
        ),
    )


def mock_summary(data: SummaryInput) -> SummaryOutput:
    char = data.character
    return SummaryOutput(
        title="黑鸦古堡的午夜钟声",
        story_summary=(
            f"本局中，{char.profession}{char.name}抵达黑鸦古堡，发现大厅钟摆异常，"
            "并从老管家口中得知「午夜钟声」的关键线索。虽然最初观察大厅失败，"
            "但通过后续行动，艾琳确认失踪学者与午夜钟声有关。"
            "下一步建议调查东侧走廊和钟摆背后的机关。"
        ),
        key_choices=["观察大厅", "与老管家交涉"],
        ending_type="open",
        next_suggestion="调查东侧走廊和钟摆机关",
    )
