# -*- coding: utf-8 -*-
"""种子数据 — 初始化管理员、世界观、测试角色与测试会话

admin 密码从环境变量 SEED_ADMIN_PASSWORD 读取(默认 admin123, 仅限开发),
用 bcrypt 加密后入库, 真实密码不出现在仓库中。

用法:
    python -m app.db.seed_data
幂等性: 依据 username / world name 去重, 重复执行不会产生脏数据。
"""
import json
import os

import bcrypt
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import ActionCheck, Character, Clue, GameSession, Message, Task, User, World

# ---------------- 世界观数据 ----------------

WORLDS = [
    dict(
        name="奇幻遗迹",
        type="fantasy",
        description="失落王国的地下遗迹重见天日，传闻深处沉睡着古代魔法与守卫。冒险者们受雇于学院，深入遗迹探明真相。",
        opening_prompt=(
            "你是一名经验丰富的 D&D 地下城主。世界观：剑与魔法的奇幻大陆，玩家受魔法学院委托进入新发现的地下遗迹。"
            "基调：探索与解谜为主，战斗为辅。请以第二人称描写开场：玩家站在遗迹入口，给出 2-3 个可行动方向。"
            "叙事每次不超过 200 字，涉及不确定结果的行动需提示玩家进行检定。"
        ),
    ),
    dict(
        name="古堡悬疑",
        type="mystery",
        description="暴风雨夜，你受邀来到山顶古堡赴宴，午夜钟声敲响时主人却离奇失踪。宾客各怀心事，真相藏在走廊尽头。",
        opening_prompt=(
            "你是一名擅长悬疑推理的跑团主持人。世界观：近代哥特风古堡，一桩失踪案在暴风雨夜发生。"
            "基调：调查、对话与线索收集为主。请以第二人称描写开场：钟声、停电与仆人的惊叫，给出 2-3 个初始调查方向。"
            "叙事每次不超过 200 字，玩家搜证/说服/洞察等行动需提示进行相应技能检定，并逐步发放线索。"
        ),
    ),
    dict(
        name="追捕克仑可 Krenko's Way",
        type="mystery",
        description=(
            "拉尼卡第十区。恶名昭彰的鬼怪黑帮头目克仑可在转狱途中越狱，十会盟督学纳休斯·文雇你将其活捉归案。"
            "敌对帮派\u201c骚帮兄弟会\u201d同样在全城搜捕他——为复仇，也为地盘。你只有三天时间，"
            "线索藏在下水道、锡街与锻炉街之间。（为 1 级角色设计的调查向短途冒险）"
        ),
        opening_prompt=(
            "你是熟悉拉尼卡设定的 D&D 5e 主持人，运行短途冒险《追捕克仑可》。基调：都市调查与帮派斗争，战斗为辅。"
            "叙事用第二人称，每次不超过 200 字，结尾给出 2-3 个行动方向；涉及不确定结果时要求玩家检定（DC 范围 5-30）。"
            "【背景】鬼怪黑帮头目克仑可因谋杀骚帮兄弟会三弟达吉等罪行被判终身监禁，今晨转狱去乌泽途中被神秘势力救走。"
            "骚帮兄弟会剩下的两兄弟里金与加德吉誓要杀他复仇。"
            "【开局】十会盟督学纳休斯·文（维多肯，说话拘谨、回避审问相关问题）召见小队：活捉克仑可送到区边缘的瑟雷尼亚旧粮仓，"
            "不得私自审问；预付 10 奇诺，事成再付 100。DC15 感知(洞悉)可察觉他有所隐瞒（他实为幕后雇主办事）。"
            "【三条调查线】1) 广场西下水道：DC10 察觉找到被撬的格栅，DC15 力量拉开；井下靴印 DC15 求生追踪（每过一天 DC+5），"
            "隧道通向锻炉街运河码头的旧仓库。2) 锡街：骚帮地盘。军火商法莉什住此，向克仑可供货，日落在锻炉街烟房旅馆外交货；"
            "若调查张扬，骚帮耳目伊柯（携炽火胶）会跟踪小队，DC10 威吓可让他招出效力对象。3) 锻炉街：克仑可帮派地盘，"
            "打探半小时内会引来六名鬼怪帮众驱赶；DC20 威吓或游说（贿赂 10 金优势）可问出藏身处。收集谣言：1d6 小时后 DC15 魅力(游说)。"
            "【时间线（未受干扰时）】第1天：克仑可入住运河仓库、向法莉什订武器。第2天：骚帮获知消息全员搜捕，傍晚在锻炉街制造爆炸。"
            "第3天黎明前：骚帮炸毁仓库（克仑可幸存逃散）；中午波洛斯军团平乱。玩家行动会改变这条线。"
            "【最终对决】仓库高40尺、有台道与哨兵，克仑可携两名跟班藏于办公室。他血量过半会奔向库内装置逃往运河。"
            "被俘后会游说：声称杀达吉是自卫、指认纳休斯是傀儡贪官（DC16 洞悉可看出他部分撒谎）、愿以保险箱财物换自由。"
            "【结局】移交时纳休斯带着六名暗哨；他不透露克仑可去向。可暗示幕后雇主的存在，为后续冒险留钩子。"
            "奖励：完成委托获报酬与 1 点公会声望，角色升至 2 级。"
        ),
    ),
]

# ---------------- 种子逻辑 ----------------


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def seed_admin(db: Session) -> User:
    admin = db.query(User).filter_by(username="admin").first()
    if admin:
        print("admin 已存在, 跳过")
        return admin
    password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
    admin = User(username="admin", password_hash=_hash_password(password),
                 nickname="主持人", role="admin")
    db.add(admin)
    db.flush()
    print(f"已创建 admin (id={admin.id})"
          + ("" if os.getenv("SEED_ADMIN_PASSWORD") else " [警告: 使用默认密码, 仅限开发]"))
    return admin


def seed_worlds(db: Session, admin: User) -> None:
    for w in WORLDS:
        if db.query(World).filter_by(name=w["name"]).first():
            print(f"世界观[{w['name']}] 已存在, 跳过")
            continue
        db.add(World(created_by=admin.id, rule_style="lite_dnd", difficulty="normal", **w))
        print(f"已创建世界观[{w['name']}]")


def seed_test_data(db: Session, admin: User) -> None:
    """测试角色 + 测试会话(含消息/判定/线索/任务各一条, 供联调与统计演示)"""
    if db.query(Character).filter_by(name="灰羽").first():
        print("测试数据已存在, 跳过")
        return
    char = Character(
        user_id=admin.id, name="灰羽",
        race_id="human", class_id="rogue", background_id="acolyte",
        motivation="欠了俄佐立一笔人情，想借这次委托一笔勾销",
        hp=10, max_hp=10, hit_dice="d8", proficiency_bonus=2,
        strength=11, dexterity=16, constitution=14,
        intelligence=14, wisdom=13, charisma=12,
        skills_json=json.dumps({"inv": {"proficient": True}, "per": {"proficient": True},
                                "ste": {"proficient": True}, "prc": {"proficient": True}}),
        saving_throws_json=json.dumps(["dexterity", "intelligence"]),
        inventory_json=json.dumps(["盗贼工具", "短剑", "轻弩", "连帽斗篷", "10 奇诺预付金"],
                                  ensure_ascii=False),
    )
    db.add(char)
    db.flush()

    world = db.query(World).filter(World.name.like("追捕克仑可%")).first()
    session = GameSession(user_id=admin.id, world_id=world.id, character_id=char.id,
                          title="追捕克仑可·第一夜", current_scene="锯齿监狱·会见纳休斯",
                          current_task="接受十会盟委托")
    db.add(session)
    db.flush()

    msg = Message(session_id=session.id, sender_type="player",
                  content="我盯着纳休斯的眼睛，判断他是否有所隐瞒", message_type="action")
    db.add(msg)
    db.flush()

    db.add(ActionCheck(session_id=session.id, message_id=msg.id,
                       action_text="识破纳休斯的隐瞒", check_type="skill",
                       skill_key="ins", attribute_used="wisdom",
                       dc=15, dice_roll=14, ability_modifier=1, skill_bonus=0,
                       final_value=15, is_success=1,
                       result_text="你注意到他的眼神在回避审问相关的问题"))
    db.add(Clue(session_id=session.id, title="纳休斯有所隐瞒",
                content="谈及\u201c为何不能审问克仑可\u201d时他眼神游移", importance="key"))
    db.add(Task(session_id=session.id, title="活捉克仑可",
                description="三天内找到并活捉克仑可，送往瑟雷尼亚旧粮仓，不得私自审问",
                status="doing"))
    print(f"已创建测试角色[灰羽]与测试会话[追捕克仑可·第一夜] (session_id={session.id})")


def run() -> None:
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        seed_worlds(db, admin)
        seed_test_data(db, admin)
        db.commit()
        print("种子数据写入完成")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
