# -*- coding: utf-8 -*-
"""StoryForge 数据库初始化与校验脚本
1. 依据 schema.sql 建表, seed.sql 写入种子数据
2. 插入一条完整业务链路样例(角色→会话→消息→判定→线索→报告)
3. 校验: 外键约束生效 / 枚举 CHECK 生效 / 与 rules/dnd5e/*.json 键值对齐
用法: python init_and_verify.py [rules_dir] [db_path]
"""
import json, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).parent
RULES = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "StoryForge-Frontend/rules/dnd5e"
DB = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "storyforge.db"

def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript("PRAGMA foreign_keys = ON;")
    con.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    con.executescript((HERE / "seed.sql").read_text(encoding="utf-8"))
    con.execute("PRAGMA foreign_keys = ON")

    # ---- 样例业务链路 ----
    con.execute("""INSERT INTO characters
        (user_id,name,race_id,class_id,background_id,motivation,hp,max_hp,hit_dice,
         strength,dexterity,constitution,intelligence,wisdom,charisma,
         skills_json,saving_throws_json) VALUES
        (1,'夜影','high-elf','rogue','acolyte','寻找失踪的师父',10,10,'d8',
         10,16,14,13,12,8,
         '{"ste":{"proficient":true},"prc":{"proficient":true}}',
         '["dexterity","intelligence"]')""")
    con.execute("""INSERT INTO sessions (user_id,world_id,character_id,title,current_scene)
                   VALUES (1,2,1,'古堡第一夜','大厅·停电')""")
    con.execute("""INSERT INTO messages (session_id,sender_type,content,message_type)
                   VALUES (1,'player','我贴着墙壁潜行到走廊尽头','action')""")
    con.execute("""INSERT INTO action_checks
        (session_id,message_id,action_text,check_type,skill_key,attribute_used,
         dc,dice_roll,ability_modifier,skill_bonus,final_value,is_success,result_text)
        VALUES (1,1,'贴墙潜行','skill','ste','dexterity',15,13,3,2,18,1,'你悄无声息地滑入阴影')""")
    con.execute("INSERT INTO clues (session_id,title,content,importance) VALUES (1,'带泥的靴印','通向地窖方向','important')")
    con.execute("INSERT INTO reports (session_id,title,story_summary,ending_type) VALUES (1,'古堡阴影下的低语','玩家发现了地窖的秘密','open')")
    con.commit()

    ok = True
    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # ---- 约束校验 ----
    def must_fail(sql):
        try:
            con.execute(sql); con.rollback(); return False
        except sqlite3.IntegrityError:
            return True
    check("外键约束: 不存在的 session_id 应被拒绝",
          must_fail("INSERT INTO messages (session_id,sender_type,content,message_type) VALUES (999,'player','x','action')"))
    check("枚举约束: 非法 message_type 应被拒绝",
          must_fail("INSERT INTO messages (session_id,sender_type,content,message_type) VALUES (1,'player','x','emoji')"))
    check("范围约束: DC=99 应被拒绝",
          must_fail("INSERT INTO action_checks (session_id,action_text,dc) VALUES (1,'x',99)"))
    check("一对一约束: 同一 session 第二份 report 应被拒绝",
          must_fail("INSERT INTO reports (session_id) VALUES (1)"))
    check("JSON 约束: 非法 skills_json 应被拒绝",
          must_fail("INSERT INTO characters (user_id,name,skills_json) VALUES (1,'坏数据','{oops')"))

    # ---- 与规则 JSON 的键值对齐校验 ----
    races  = {r["id"] for r in json.loads((RULES/"races.json").read_text())["races"]}
    classes= {c["id"] for c in json.loads((RULES/"classes.json").read_text())["classes"]}
    bgs    = {b["id"] for b in json.loads((RULES/"backgrounds.json").read_text())["backgrounds"]}
    skills = set(json.loads((RULES/"skills.json").read_text())["skills"].keys())
    abils  = {v["key"] for v in json.loads((RULES/"abilities.json").read_text()).values()}

    for name, rid, cid, bid, sj, stj in con.execute(
            "SELECT name,race_id,class_id,background_id,skills_json,saving_throws_json FROM characters"):
        check(f"角色[{name}] race_id 合法", rid in races, rid)
        check(f"角色[{name}] class_id 合法", cid in classes, cid)
        check(f"角色[{name}] background_id 合法", bid in bgs, bid)
        bad_sk = set(json.loads(sj)) - skills
        check(f"角色[{name}] skills_json 键合法", not bad_sk, str(bad_sk) if bad_sk else "")
        bad_sv = set(json.loads(stj)) - abils
        check(f"角色[{name}] saving_throws 合法", not bad_sv, str(bad_sv) if bad_sv else "")
    for sk, ab in con.execute("SELECT skill_key,attribute_used FROM action_checks"):
        check("判定 skill_key 合法", sk in skills, sk)
        check("判定 attribute_used 合法", ab in abils, ab)

    # ---- 结构与数据概览 ----
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    check("表数量 = 9", len(tables) == 9, str(tables))
    idx = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")]
    check("索引数量 >= 3(规格书要求)", len(idx) >= 3, str(idx))
    print("\n--- 各表行数 ---")
    for t in tables:
        print(f"  {t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    print("\n--- 判定记录联查(答辩演示查询) ---")
    for row in con.execute("""
        SELECT c.name, a.skill_key, a.dice_roll||'+'||a.ability_modifier||'+'||a.skill_bonus
               ||'='||a.final_value, 'DC'||a.dc,
               CASE a.is_success WHEN 1 THEN '成功' ELSE '失败' END
        FROM action_checks a
        JOIN sessions s ON a.session_id=s.id
        JOIN characters c ON s.character_id=c.id"""):
        print(" ", row)
    con.close()
    print("\n结果:", "全部通过 ✔" if ok else "存在失败项 ✘")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
