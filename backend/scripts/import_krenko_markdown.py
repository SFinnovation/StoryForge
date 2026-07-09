from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "storyforge.db"

RULEBOOK_TITLE = "5e D&D 玩家手册 PHB 中译规则摘要"
MODULE_TITLE = "追捕克伦可 / 追捕克仑可 / Krenko's Way"


def now() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ", timespec="microseconds")


def read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def clean(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##+\s+{re.escape(heading)}.*?\n(?P<body>.*?)(?=^##+\s+|\Z)"
    )
    match = pattern.search(text)
    return clean(match.group("body")) if match else ""


def truncate(text: str, limit: int) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def fact(content: str, importance: str = "normal", category: str = "") -> dict[str, str]:
    return {
        "content": content,
        "importance": importance,
        "category": category,
        "source_ref": "import_krenko_markdown.py",
    }


def module_fact(
    content: str,
    fact_type: str,
    *,
    related_scene: str = "",
    importance: str = "normal",
    npc_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "content": content,
        "fact_type": fact_type,
        "related_scene": related_scene,
        "importance": importance,
        "npc_id": npc_id,
        "source_ref": "import_krenko_markdown.py",
    }


def npc(
    npc_id: str,
    name: str,
    description: str,
    *,
    personality: str = "",
    knowledge_scope: list[str] | None = None,
    forbidden_knowledge: list[str] | None = None,
    speaking_style: str = "",
    current_scene: str = "",
) -> dict[str, Any]:
    return {
        "npc_id": npc_id,
        "name": name,
        "description": description,
        "personality": personality,
        "knowledge_scope": knowledge_scope or [],
        "forbidden_knowledge": forbidden_knowledge or [],
        "speaking_style": speaking_style,
        "current_scene": current_scene,
    }


def opening_npc(npc_id: str, name: str, description: str) -> dict[str, str]:
    return {"npc_id": npc_id, "name": name, "description": description}


def build_rulebook(phb_text: str, source_name: str) -> dict[str, Any]:
    headings = set(re.findall(r"(?m)^#{2,3}\s+(.+)$", phb_text))
    useful_topics = [
        "二十面骰 / The D20",
        "优势与劣势 / Advantage and Disadvantage",
        "属性值和调整值 / Ability Scores and Modifiers",
        "熟练加值 / Proficiency Bonus",
        "护甲等级 / Armor Class",
        "生命值与生命骰 / Hit Point and Hit Dice",
    ]
    found_topics = [topic for topic in useful_topics if topic in headings]
    public_facts = [
        fact("D&D 5e 用 d20 作为主要判定：d20 + 属性调整值 + 熟练加值，与 DC 或对抗结果比较。", "key", "rules"),
        fact("优势掷两个 d20 取高，劣势掷两个 d20 取低；多重优势/劣势通常不叠加。", "key", "rules"),
        fact("1 级角色熟练加值为 +2，可加入已熟练的技能、豁免、武器或工具判定。", "key", "rules"),
        fact("战斗与危险行动优先使用清晰的行动后果、DC、护甲等级、生命值、豁免和伤害来裁定。", "normal", "rules"),
        fact("角色创建包含种族、职业、属性、背景、装备与角色关系，适合服务冒险叙事。", "normal", "character"),
    ]
    world_setting = (
        "Dungeons & Dragons 第五版是以合作叙事、角色扮演、探索、社交和战斗为核心的奇幻冒险规则系统。"
        "本规则包为 StoryForge 提供轻量判定依据，不作为开局剧情素材；具体故事素材优先来自已绑定冒险模组。"
    )
    core_rules = (
        "轻量 D&D 5e 裁定摘要：常规检定使用 d20 + 属性调整值 + 熟练加值，对比 DC。"
        "1 级角色熟练加值为 +2。优势/劣势以两个 d20 取高/取低表现。"
        "行动失败时应推进局势并给出代价，成功时给出清晰收益。"
        "战斗相关行动可参考 AC、生命值、伤害、豁免、先攻和位置关系。"
        "除非玩家明确请求，不要让规则摘要覆盖当前冒险模组的地点、NPC 和任务。"
    )
    if found_topics:
        core_rules += f" 已在源文件中识别到关键规则段落：{', '.join(found_topics)}。"
    return {
        "title": RULEBOOK_TITLE,
        "source_filename": source_name,
        "world_setting": world_setting,
        "world_style": "D&D 5e 轻量规则；英雄冒险；清晰判定；失败也推动剧情。",
        "public_world_facts_json": json_dump(public_facts),
        "core_rules_summary": core_rules,
        "extraction_notes": f"Imported from markdown; source length={len(phb_text)} chars.",
        "knowledge_pack_dir": None,
        "status": "active",
    }


def build_module(krenko_text: str, source_name: str) -> dict[str, Any]:
    story_overview = section(krenko_text, "故事梗概 / Story Overview")
    adventure_summary = section(krenko_text, "冒险摘要 / Adventure Summary")
    starting = section(krenko_text, "开始冒险 / Starting the Adventure")
    dossier = section(krenko_text, "卷宗 / The Dossier")
    timeline = section(krenko_text, "事件时间线 / Timeline of Events")
    falish = section(krenko_text, "法莉什的工坊 / Falish's Workshop")
    hideout = section(krenko_text, "克仑可的藏身处 / Krenko's Hideout")
    confrontation = section(krenko_text, "直面克仑可 / Confronting Krenko")

    story_summary = "\n\n".join(
        [
            "《追捕克伦可 / Krenko's Way》是发生在拉尼卡第十区的 D&D 5e 1 级短冒险。"
            "鬼怪暴民头目克伦可在转狱途中逃脱，十会盟官员纳休斯·文雇佣冒险者追捕他并活着带回。",
            "冒险核心流程是：从锯齿监狱接受委托，追查转狱路线、警卫、线人和城市流言，避免或应对骚帮兄弟会的介入，最终找到运河附近仓库中的克伦可。",
            truncate(adventure_summary, 1200),
        ]
    )

    opening_prompt = (
        "你正在主持 D&D 5e 冒险《追捕克伦可 / Krenko's Way》。必须使用拉尼卡第十区作为舞台，"
        "开局地点是锯齿监狱或十会盟安排的会面处，委托人是纳休斯·文 Nassius Ven。"
        "核心事件：鬼怪暴民头目克伦可在转狱途中逃脱，玩家需要调查线索，避开或处理骚帮兄弟会，"
        "最终找到克伦可并尽量活捉交还。不要生成剑湾、渡鸦谷、龙骨山脉或其他通用 D&D 地点。"
        "叙事风格应是城市追捕、帮派压力、拉尼卡公会政治、低等级冒险和清晰调查线索。"
    )

    scenes = [
        {
            "scene_id": "sawtooth_prison_briefing",
            "title": "锯齿监狱委托",
            "description": "纳休斯·文向角色说明克伦可越狱、转狱路线和必须活捉的要求，并交付卷宗。",
            "exits": ["the_search_for_krenko", "dossier_review"],
            "points_of_interest": ["纳休斯·文", "克伦可卷宗", "十奇诺启动经费", "不得私自审问的警告"],
        },
        {
            "scene_id": "the_search_for_krenko",
            "title": "走上街头",
            "description": "角色在第十区调查克伦可的下落，可会见联络人、收集谣言、访问锡街和锻炉街。",
            "exits": ["plaza_west_sewers", "falish_workshop", "foundry_street"],
            "points_of_interest": ["城市流言", "警卫证词", "骚帮耳目", "时间线压力"],
        },
        {
            "scene_id": "plaza_west_sewers",
            "title": "广场西的下水道",
            "description": "调查转狱和逃脱痕迹时，角色可能进入下水道，遭遇城市危险和残留线索。",
            "exits": ["the_search_for_krenko", "falish_workshop"],
            "points_of_interest": ["逃脱路线", "下水道遭遇", "公会影响痕迹"],
        },
        {
            "scene_id": "falish_workshop",
            "title": "法莉什的工坊",
            "description": "伊捷武器发明者法莉什可能与克伦可的武器和订单有关，是通往藏身处的重要线索。",
            "exits": ["foundry_street", "krenko_hideout"],
            "points_of_interest": ["法莉什", "武器订单", "工坊宝藏", "伊捷装置"],
        },
        {
            "scene_id": "foundry_street",
            "title": "锻炉街",
            "description": "克伦可和鬼怪帮派活动频繁的街区，骚帮兄弟会的反应会使调查迅速升温。",
            "exits": ["krenko_hideout", "shattergang_response"],
            "points_of_interest": ["骚帮兄弟会", "鬼怪帮派", "帮派地盘", "暴力威胁"],
        },
        {
            "scene_id": "krenko_hideout",
            "title": "克伦可的藏身处",
            "description": "运河附近仓库是最终藏身处，包含岗哨、换班、增援、仓库办公室、台道和主楼面。",
            "exits": ["confronting_krenko", "handoff"],
            "points_of_interest": ["仓库岗哨", "克伦可的帮派", "脆弱台阶", "主楼面", "克伦可"],
        },
    ]

    public_world_facts = [
        "冒险发生在拉尼卡 Ravnica 第十区 Tenth District。",
        "玩家受十会盟官员纳休斯·文 Nassius Ven 雇佣，目标是活捉逃脱的鬼怪暴民头目克伦可。",
        "克伦可原本被波洛斯军团关押在锯齿监狱 Sawtooth Prison，转狱途中逃脱。",
        "骚帮兄弟会 Shattergang Brothers 想找到并杀死克伦可，为达吉 Dargig 复仇。",
        "调查可从转狱路线、警卫、联络人、流言、锡街、锻炉街、法莉什和仓库线索推进。",
    ]
    hidden_truths = [
        "纳休斯·文要求活捉且不要私自审问克伦可，是因为他怀疑有一个或多个公会卷入越狱事件。",
        "克伦可在转狱途中得到某个派系或公会的帮助，具体雇主可由 DM 选择或随机决定。",
        "时间拖得越久，骚帮兄弟会越可能发现克伦可的位置，并引发更严重的帮派暴力。",
        "克伦可的藏身处在运河附近仓库；最终冲突可能同时卷入克伦可帮派和骚帮成员。",
    ]
    world_facts = [
        "拉尼卡是由公会势力、城市秩序和街头帮派交织支配的巨型城市世界。",
        "第十区的公共秩序由波洛斯军团、俄佐立参议院等组织影响，但十会盟会介入跨公会危机。",
        "低等级角色可以通过调查、社交、潜入、追踪和有限战斗推进冒险。",
    ]
    player_known_clues = [
        "克伦可今日早些时候在转狱途中逃脱。",
        "克伦可是锻炉街附近鬼怪黑帮的头目，罪行包括谋杀与武器相关袭击。",
        "骚帮兄弟会是克伦可的敌对帮派，也在寻找他。",
        "纳休斯·文提供经费用于调查，并要求把克伦可活着带回。",
    ]
    npc_private_facts = [
        module_fact("纳休斯知道任务背后可能牵涉公会政治，但不会主动透露超出委托目标的信息。", "npc_private", related_scene="sawtooth_prison_briefing", importance="key", npc_id="nassius_ven"),
        module_fact("克伦可知道是谁帮助他逃脱，也知道自己的帮派和骚帮兄弟会都在快速行动。", "npc_private", related_scene="krenko_hideout", importance="key", npc_id="krenko"),
        module_fact("法莉什可能掌握克伦可武器订单或藏身方向的线索。", "npc_private", related_scene="falish_workshop", importance="normal", npc_id="falish"),
    ]
    visible_npcs = [
        npc(
            "nassius_ven",
            "纳休斯·文 Nassius Ven",
            "维多肯，十会盟官员/督学，雇佣角色追捕克伦可。",
            personality="克制、官僚、谨慎，知道更多但不愿完全摊牌。",
            knowledge_scope=["克伦可越狱", "转狱路线", "任务报酬", "不得私自审问的要求"],
            forbidden_knowledge=["真正雇主或涉事公会的定论"],
            speaking_style="正式、精确、带有外交辞令。",
            current_scene="sawtooth_prison_briefing",
        ),
        npc(
            "krenko",
            "克伦可 Krenko",
            "鬼怪暴民头目，狡猾投机，正在重组犯罪事业。",
            personality="精明、张狂、求生欲强，会利用公会和帮派矛盾。",
            knowledge_scope=["越狱过程", "藏身处", "帮派部署", "雇主线索"],
            forbidden_knowledge=["DM 未决定的雇主最终答案"],
            speaking_style="街头化、狡诈、挑衅。",
            current_scene="krenko_hideout",
        ),
        npc(
            "falish",
            "法莉什 Falish",
            "人类伊捷武器发明者，与克伦可的武器订单和锻炉街线索有关。",
            personality="神经质、技术自负、容易被压力逼出口风。",
            knowledge_scope=["武器订单", "工坊异常", "克伦可相关交易"],
            forbidden_knowledge=["不在场的最终藏身处全貌"],
            speaking_style="快速、跳跃、夹杂技术术语。",
            current_scene="falish_workshop",
        ),
    ]
    seed_npcs = [
        opening_npc("nassius_ven", "纳休斯·文", "十会盟官员，向冒险者交付追捕克伦可的任务。"),
        opening_npc("krenko", "克伦可", "逃脱的鬼怪暴民头目，本冒险的追捕目标。"),
        opening_npc("shattergang_brothers", "骚帮兄弟会", "克伦可的敌对鬼怪帮派，想抢先找到并杀死他。"),
        opening_npc("falish", "法莉什", "可能与克伦可武器订单有关的伊捷发明者。"),
    ]

    notes = {
        "source_length": len(krenko_text),
        "sections_used": {
            "story_overview": bool(story_overview),
            "adventure_summary": bool(adventure_summary),
            "starting": bool(starting),
            "dossier": bool(dossier),
            "timeline": bool(timeline),
            "falish": bool(falish),
            "hideout": bool(hideout),
            "confrontation": bool(confrontation),
        },
    }
    return {
        "title": MODULE_TITLE,
        "source_filename": source_name,
        "story_summary": truncate(story_summary, 3000),
        "opening_prompt": opening_prompt,
        "scenes_json": json_dump(scenes),
        "current_scene": "sawtooth_prison_briefing",
        "hidden_truths_json": json_dump(hidden_truths),
        "world_facts_json": json_dump(world_facts),
        "public_world_facts_json": json_dump(public_world_facts),
        "player_known_clues_json": json_dump(player_known_clues),
        "npc_private_facts_json": json_dump(npc_private_facts),
        "visible_npcs_json": json_dump(visible_npcs),
        "seed_npcs_json": json_dump(seed_npcs),
        "extraction_notes": json_dump(notes),
        "knowledge_pack_dir": None,
        "status": "active",
    }


def upsert_by_title(
    con: sqlite3.Connection,
    table: str,
    data: dict[str, Any],
) -> int:
    existing = con.execute(f"SELECT id FROM {table} WHERE title = ?", (data["title"],)).fetchone()
    fields = [key for key in data.keys()]
    if existing:
        assignments = ", ".join(f"{field} = ?" for field in fields if field != "title")
        values = [data[field] for field in fields if field != "title"]
        values.append(existing["id"])
        con.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", values)
        return int(existing["id"])

    insert_data = dict(data)
    insert_data["created_at"] = now()
    columns = ", ".join(insert_data.keys())
    placeholders = ", ".join("?" for _ in insert_data)
    cur = con.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        list(insert_data.values()),
    )
    return int(cur.lastrowid)


def find_dnd_world(con: sqlite3.Connection) -> sqlite3.Row:
    row = con.execute(
        """
        SELECT id, name FROM worlds
        WHERE is_enabled = 1
          AND (
            name LIKE '%DND%'
            OR name LIKE '%D&D%'
            OR name LIKE '%龙与地下城%'
            OR type = 'fantasy'
          )
        ORDER BY
          CASE WHEN name LIKE '%DND%' OR name LIKE '%龙与地下城%' THEN 0 ELSE 1 END,
          id
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise SystemExit("No enabled DND/fantasy world found in worlds table.")
    return row


def import_content(db_path: Path, phb_path: Path, krenko_path: Path) -> dict[str, Any]:
    phb_text = read_md(phb_path)
    krenko_text = read_md(krenko_path)
    rulebook = build_rulebook(phb_text, phb_path.name)
    module = build_module(krenko_text, krenko_path.name)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute("BEGIN")
        rulebook_id = upsert_by_title(con, "rulebook_packs", rulebook)
        module_id = upsert_by_title(con, "adventure_modules", module)
        world = find_dnd_world(con)
        con.execute(
            """
            UPDATE worlds
            SET rulebook_pack_id = ?,
                adventure_module_id = ?,
                description = ?,
                opening_prompt = ?,
                rule_style = ?,
                type = 'fantasy'
            WHERE id = ?
            """,
            (
                rulebook_id,
                module_id,
                module["story_summary"][:2000],
                module["opening_prompt"],
                rulebook["world_style"][:500],
                world["id"],
            ),
        )
        con.commit()
        return {
            "world_id": int(world["id"]),
            "world_name": world["name"],
            "rulebook_pack_id": rulebook_id,
            "adventure_module_id": module_id,
            "rulebook_title": rulebook["title"],
            "module_title": module["title"],
        }
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import PHB + Krenko markdown into StoryForge DB.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--phb", type=Path, required=True, help="Path to the PHB markdown file")
    parser.add_argument("--krenko", type=Path, required=True, help="Path to the Krenko's Way markdown file")
    args = parser.parse_args()

    for path in [args.db, args.phb, args.krenko]:
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")

    result = import_content(args.db.resolve(), args.phb.resolve(), args.krenko.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
