"""无 LLM API Key 时的演示/mock 响应，便于本地联调。"""

from app.ai.schemas.action_parse import ActionParseInput, ActionParseOutput
from app.ai.schemas.critic import CriticOutput, CriticScores
from app.ai.schemas.narrative import NarrativeInput, NarrativeOutput, StateUpdates
from app.ai.schemas.opening import OpeningInput, OpeningNpc, OpeningOutput
from app.ai.schemas.summary import SummaryInput, SummaryOutput


def mock_rulebook_extract(data) -> "RulebookExtractionOutput":
    from app.ai.schemas.rulebook_extract import RulebookExtractionOutput, WorldFactItem

    title = data.source_name if hasattr(data, "source_name") else "D&D 5e 玩家手册"
    return RulebookExtractionOutput(
        title=title,
        world_setting=(
            "费伦大陆风格的奇幻世界，冒险者以小队形式探索地下城、城市与荒野。"
            "神祇与魔法真实存在，社会由王国、城邦与公会共同维系。"
            "玩家扮演英雄，通过属性检定与技能应对探索、社交与战斗挑战。"
        ),
        world_style="奇幻冒险·英雄主义·中等难度·第二人称叙事·规则轻量 d20",
        public_world_facts=[
            WorldFactItem(content="六大属性决定角色能力：力量、敏捷、体质、智力、感知、魅力。", category="规则"),
            WorldFactItem(content="d20 检定：掷骰 + 属性修正 + 熟练加值，结果不低于 DC 则成功。", category="规则", importance="key"),
            WorldFactItem(content="优势掷两次取高，劣势掷两次取低。", category="规则"),
            WorldFactItem(content="短休可花费生命骰恢复 HP，长休可恢复大部分资源。", category="规则"),
        ],
        core_rules_summary=(
            "属性修正 = floor((属性值-10)/2)。技能检定关联特定属性。"
            "1级熟练加值 +2。战斗轮以先攻排序，攻击为 d20+修正 vs AC。"
        ),
        extraction_notes="mock 模式：未调用 LLM，返回 PHB 轻量规则摘要占位。",
    )


def mock_module_extract(data) -> "ModuleExtractionOutput":
    from app.ai.schemas.module_extract import (
        ModuleExtractionOutput,
        ModuleFactItem,
        ModuleNpcSeed,
        ModuleScene,
    )
    from app.ai.schemas.opening import OpeningNpc

    name = getattr(data, "source_name", "追捕克仑可")
    is_krenko = "克仑" in name or "krenko" in name.lower()
    title = "追捕克仑可" if is_krenko else name

    return ModuleExtractionOutput(
        title=title,
        story_summary=(
            "拉尼卡第十区，狗头人黑帮头目克仑可（Krenko）控制了地精帮派。"
            "玩家受公会委托追踪克仑可，需在其据点与街头眼线之间周旋，"
            "最终将其绳之以法或逼其现身。模组强调城市追逐、社交刺探与小规模战斗。"
        ),
        opening_prompt=(
            "拉尼卡第十区街头，潮湿而喧嚣。公会联络人交给你一张潦草地图，"
            "指向克仑可可能出没的赌场后巷。你需要组建小队，从眼线处获取情报，"
            "在不惊动整个帮派的情况下逼近目标。"
        ),
        scenes=[
            ModuleScene(
                scene_id="tenth_district_street",
                title="第十区主街",
                description="喧闹的集市与酒馆林立，帮派眼线四处游荡。",
                exits=["gambling_alley", "guild_safehouse"],
                points_of_interest=["公告板", "可疑的地精信使"],
            ),
            ModuleScene(
                scene_id="gambling_alley",
                title="赌场后巷",
                description="狭窄阴暗，通往克仑可地下据点入口。",
                exits=["tenth_district_street", "krenko_hideout"],
                points_of_interest=["上锁铁门", "脚印与鳞片痕迹"],
            ),
            ModuleScene(
                scene_id="krenko_hideout",
                title="克仑可藏身处",
                description="地下密室，狗头人与地精混杂。",
                exits=["gambling_alley"],
                points_of_interest=["克仑可的宝座", "赃物箱"],
            ),
        ],
        current_scene="tenth_district_street",
        hidden_truths=[
            "克仑可已与外来恶魔信徒秘密结盟，真正目标是夺取公会封印石。",
            "赌场后巷铁门钥匙由双面间谍持有，他同时向公会卖情报。",
        ],
        world_facts=["拉尼卡由十大公会共同维持秩序。"],
        public_world_facts=[
            "克仑可是第十区臭名昭著的地精黑帮头目。",
            "公会悬赏高额赏金追捕克仑可。",
        ],
        player_known_clues=["联络人提供的潦草地图指向赌场后巷。"],
        npc_private_facts=[
            ModuleFactItem(
                content="铁门钥匙在我这里，但别告诉克仑可。",
                fact_type="npc_private",
                npc_id="spy_double_001",
                importance="important",
            ),
        ],
        visible_npcs=[
            ModuleNpcSeed(
                npc_id="guild_contact_001",
                name="公会联络人",
                description="谨慎的精灵信使",
                personality="务实、紧迫",
                knowledge_scope=["公会任务", "克仑可行踪传闻"],
                forbidden_knowledge=["恶魔信徒结盟"],
                speaking_style="简短、压低声音",
                current_scene="tenth_district_street",
            ),
        ],
        seed_npcs=[
            OpeningNpc(npc_id="guild_contact_001", name="公会联络人", description="交给你地图的精灵信使"),
        ],
        extraction_notes="mock 模式：追捕克仑可模组占位数据。",
    )


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
