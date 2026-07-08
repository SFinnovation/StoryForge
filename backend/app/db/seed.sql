-- ============================================================
-- StoryForge · 初始化种子数据（依据 implementation-spec.md §6.4）
-- 注意: admin 的 password_hash 为占位符, 实际部署时由
--       backend/app/db/init_data.py 读取 .env(SEED_ADMIN_PASSWORD)
--       用 bcrypt 生成后写入, 切勿在仓库中提交真实哈希。
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. 管理员账号
INSERT INTO users (username, password_hash, nickname, role)
VALUES ('admin', '$2b$12$PLACEHOLDER_SET_BY_INIT_DATA_FROM_ENV', '主持人', 'admin');

-- 2. 世界观一：奇幻遗迹（fantasy）
INSERT INTO worlds (name, type, description, opening_prompt, rule_style, difficulty, created_by)
VALUES (
    '奇幻遗迹',
    'fantasy',
    '失落王国的地下遗迹重见天日，传闻深处沉睡着古代魔法与守卫。冒险者们受雇于学院，深入遗迹探明真相。',
    '你是一名经验丰富的 D&D 地下城主。世界观：剑与魔法的奇幻大陆，玩家受魔法学院委托进入新发现的地下遗迹。' ||
    '基调：探索与解谜为主，战斗为辅。请以第二人称描写开场：玩家站在遗迹入口，给出 2-3 个可行动方向。' ||
    '叙事每次不超过 200 字，涉及不确定结果的行动需提示玩家进行检定。',
    'lite_dnd',
    'normal',
    1
);

-- 3. 世界观二：古堡悬疑（mystery）
INSERT INTO worlds (name, type, description, opening_prompt, rule_style, difficulty, created_by)
VALUES (
    '古堡悬疑',
    'mystery',
    '暴风雨夜，你受邀来到山顶古堡赴宴，午夜钟声敲响时主人却离奇失踪。宾客各怀心事，真相藏在走廊尽头。',
    '你是一名擅长悬疑推理的跑团主持人。世界观：近代哥特风古堡，一桩失踪案在暴风雨夜发生。' ||
    '基调：调查、对话与线索收集为主。请以第二人称描写开场：钟声、停电与仆人的惊叫，给出 2-3 个初始调查方向。' ||
    '叙事每次不超过 200 字，玩家搜证/说服/洞察等行动需提示进行相应技能检定，并逐步发放线索。',
    'lite_dnd',
    'normal',
    1
);
