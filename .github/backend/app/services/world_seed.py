# -*- coding: utf-8 -*-
"""World Seed (implementation §2.1 / §6.2)

开局时把模组静态数据灌入会话:
  facts        <- world_public / hidden_truth / npc_private (allow_protected 通道)
  npc_profiles <- NPC 人格与知识边界

模组数据按 worlds.name 匹配; 未收录的世界观(如自定义)不 seed, 不报错。
幂等: FactRepo 不去重但本函数以"该会话已有 world_public"为已 seed 标志跳过。
"""
from sqlalchemy.orm import Session

from ..db.models import World
from ..repositories import FactRepo, NpcRepo, SessionRepo

# ---------------- 模组数据 ----------------

MODULE_DATA: dict[str, dict] = {
    "古堡悬疑": {
        "facts": [
            dict(content="古堡主人在午夜钟声敲响时失踪, 全堡停电十分钟。",
                 fact_type="world_public", importance="important"),
            dict(content="失踪学者生前在研究古堡地下室的一份手稿。",
                 fact_type="world_public"),
            dict(content="地下室入口位于东侧走廊尽头的画像后。",
                 fact_type="hidden_truth", importance="key",
                 status="locked", related_scene="east_corridor"),
            dict(content="老管家昨晚看见学者独自进入东侧走廊。",
                 fact_type="npc_private", related_scene="main_hall"),
        ],
        "npcs": [
            dict(npc_id="butler_001", name="老管家",
                 personality="谨慎、回避、忠诚于古堡主人",
                 knowledge_scope=["古堡日常", "地下室钥匙", "学者昨晚进东侧走廊"],
                 forbidden_knowledge=["最终 Boss 身份", "密室机关完整解法"],
                 speaking_style="礼貌、含糊、敬语", related_scene="main_hall"),
        ],
    },
    "追捕克仑可 Krenko's Way": {
        "facts": [
            dict(content="十会盟悬赏活捉越狱的鬼怪黑帮头目克仑可, 期限三天。",
                 fact_type="world_public", importance="key"),
            dict(content="骚帮兄弟会同样在全城搜捕克仑可, 为复仇也为地盘。",
                 fact_type="world_public"),
            dict(content="克仑可藏身于锻炉街运河码头的旧仓库。",
                 fact_type="hidden_truth", importance="key",
                 status="locked", related_scene="forge_street"),
            dict(content="纳休斯·文实为幕后雇主办事, 并非单纯执法。",
                 fact_type="hidden_truth", importance="key", status="locked"),
            dict(content="军火商法莉什将于日落在烟房旅馆外向克仑可交货。",
                 fact_type="npc_private", related_scene="tin_street"),
        ],
        "npcs": [
            dict(npc_id="lavinia_001", name="纳休斯·文",
                 personality="维多肯, 说话拘谨, 回避审问相关问题",
                 knowledge_scope=["委托内容", "报酬 10+100 奇诺", "移交地点瑟雷尼亚旧粮仓"],
                 forbidden_knowledge=["幕后雇主身份"],
                 speaking_style="正式、官腔", related_scene="锯齿监狱·会见纳休斯"),
            dict(npc_id="falish_001", name="法莉什",
                 personality="精明的军火商, 只认钱",
                 knowledge_scope=["武器交易", "克仑可的订单"],
                 forbidden_knowledge=["克仑可确切藏身处"],
                 speaking_style="市侩、警惕", related_scene="tin_street"),
        ],
    },
}


def seed_session_world_data(db: Session, session_id: int) -> dict:
    """开局调用: 依据会话所属世界观灌入模组 facts + npc_profiles。

    返回 {"facts": n, "npcs": n, "skipped": bool}
    """
    session = SessionRepo(db).get(session_id)
    if session is None:
        raise ValueError(f"session {session_id} 不存在")
    world = db.get(World, session.world_id)
    module = MODULE_DATA.get(world.name if world else "")
    if module is None:
        return {"facts": 0, "npcs": 0, "skipped": True}

    facts = FactRepo(db)
    if facts.list_by_session(session_id, fact_types=["world_public"]):
        return {"facts": 0, "npcs": 0, "skipped": True}  # 已 seed, 幂等跳过

    n_facts = 0
    for f in module["facts"]:
        facts.create(session_id, f["content"], f["fact_type"],
                     related_scene=f.get("related_scene"),
                     importance=f.get("importance", "normal"),
                     status=f.get("status", "active"),
                     allow_protected=True)   # 唯一允许创建 hidden/npc_private 的通道
        n_facts += 1
    npcs = NpcRepo(db).create_batch(session_id, module["npcs"])
    return {"facts": n_facts, "npcs": len(npcs), "skipped": False}
