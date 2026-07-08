-- ============================================================
-- StoryForge 灵境档案 · 数据库建表脚本（SQLite 友好）
-- 依据: docs/implementation-spec.md §6 数据模型
-- 约定: 静态规则数据存于 rules/dnd5e/*.json, 不入库;
--       characters/action_checks 通过字符串键(race_id/class_id/
--       background_id/skill_key)与规则 JSON 对接。
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 1. 用户
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nickname      TEXT,
    role          TEXT NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user', 'admin')),
    avatar_url    TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. 世界观
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS worlds (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    type           TEXT NOT NULL
                   CHECK (type IN ('fantasy', 'mystery', 'cyberpunk', 'custom')),
    description    TEXT,
    opening_prompt TEXT,                    -- AI 开局 system 上下文
    rule_style     TEXT DEFAULT 'lite_dnd',
    difficulty     TEXT DEFAULT 'normal',
    cover_url      TEXT,
    created_by     INTEGER REFERENCES users(id),
    is_public      INTEGER DEFAULT 1 CHECK (is_public IN (0, 1)),
    is_enabled     INTEGER DEFAULT 1 CHECK (is_enabled IN (0, 1)),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. 角色（D&D 5e 字段整合）
--    race_id / class_id / background_id 对应 rules/dnd5e/*.json 的 id
--    skills_json 例: {"ste":{"proficient":true}}  键为 skills.json 的技能键
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS characters (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(id),
    name               TEXT NOT NULL,
    race_id            TEXT,               -- dnd5e: high-elf, human, ...
    class_id           TEXT,               -- dnd5e: rogue, fighter, ...
    background_id      TEXT,               -- dnd5e: acolyte, ...
    motivation         TEXT,
    level              INTEGER DEFAULT 1  CHECK (level BETWEEN 1 AND 20),
    exp                INTEGER DEFAULT 0  CHECK (exp >= 0),
    hp                 INTEGER DEFAULT 10,
    max_hp             INTEGER DEFAULT 10 CHECK (max_hp > 0),
    hit_dice           TEXT DEFAULT 'd8',
    proficiency_bonus  INTEGER DEFAULT 2,
    strength           INTEGER NOT NULL DEFAULT 10 CHECK (strength     BETWEEN 1 AND 30),
    dexterity          INTEGER NOT NULL DEFAULT 10 CHECK (dexterity    BETWEEN 1 AND 30),
    constitution       INTEGER NOT NULL DEFAULT 10 CHECK (constitution BETWEEN 1 AND 30),
    intelligence       INTEGER NOT NULL DEFAULT 10 CHECK (intelligence BETWEEN 1 AND 30),
    wisdom             INTEGER NOT NULL DEFAULT 10 CHECK (wisdom       BETWEEN 1 AND 30),
    charisma           INTEGER NOT NULL DEFAULT 10 CHECK (charisma     BETWEEN 1 AND 30),
    skills_json        TEXT DEFAULT '{}' CHECK (json_valid(skills_json)),
    saving_throws_json TEXT DEFAULT '[]' CHECK (json_valid(saving_throws_json)),
    inventory_json     TEXT DEFAULT '[]' CHECK (json_valid(inventory_json)),
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 4. 跑团会话
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    world_id      INTEGER NOT NULL REFERENCES worlds(id),
    character_id  INTEGER NOT NULL REFERENCES characters(id),
    title         TEXT,
    status        TEXT NOT NULL DEFAULT 'playing'
                  CHECK (status IN ('playing', 'finished', 'archived')),
    current_scene TEXT,
    current_task  TEXT,
    summary       TEXT,
    started_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at      DATETIME
);

-- ------------------------------------------------------------
-- 5. 消息日志
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id),
    sender_type  TEXT NOT NULL
                 CHECK (sender_type IN ('player', 'ai', 'npc', 'system')),
    sender_name  TEXT,
    content      TEXT NOT NULL,
    message_type TEXT NOT NULL
                 CHECK (message_type IN ('narration', 'action', 'dialogue',
                                         'dice', 'clue', 'task')),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 6. 行动判定
--    skill_key 对应 rules/dnd5e/skills.json 的键 (如 ste)
--    attribute_used 对应 abilities.json 的 key (如 dexterity)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS action_checks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       INTEGER NOT NULL REFERENCES sessions(id),
    message_id       INTEGER REFERENCES messages(id),
    action_text      TEXT NOT NULL,
    check_type       TEXT,
    skill_key        TEXT,
    attribute_used   TEXT,
    dc               INTEGER CHECK (dc IS NULL OR dc BETWEEN 5 AND 30),
    dice_roll        INTEGER CHECK (dice_roll IS NULL OR dice_roll BETWEEN 1 AND 20),
    ability_modifier INTEGER,
    skill_bonus      INTEGER DEFAULT 0,
    final_value      INTEGER,
    is_success       INTEGER CHECK (is_success IS NULL OR is_success IN (0, 1)),
    result_text      TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 7. 线索
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clues (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES sessions(id),
    title         TEXT NOT NULL,
    content       TEXT,
    source_scene  TEXT,
    importance    TEXT DEFAULT 'normal'
                  CHECK (importance IN ('normal', 'important', 'key')),
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 8. 任务
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT DEFAULT 'todo'
                CHECK (status IN ('todo', 'doing', 'done', 'failed')),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 9. 结局报告（与 session 一对一）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       INTEGER NOT NULL UNIQUE REFERENCES sessions(id),
    title            TEXT,
    story_summary    TEXT,
    key_choices_json TEXT DEFAULT '[]' CHECK (json_valid(key_choices_json)),
    clues_json       TEXT DEFAULT '[]' CHECK (json_valid(clues_json)),
    ending_type      TEXT CHECK (ending_type IS NULL OR
                                 ending_type IN ('good', 'normal', 'bad', 'open')),
    character_growth TEXT,
    ai_suggestion    TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 索引（规格书 §6.3 + 面向 P1 查询的补充）
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_user_status  ON sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_session      ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_action_checks_session ON action_checks(session_id);
-- 补充: 线索/任务面板与角色列表的常用查询路径
CREATE INDEX IF NOT EXISTS idx_clues_session         ON clues(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_session_status  ON tasks(session_id, status);
CREATE INDEX IF NOT EXISTS idx_characters_user       ON characters(user_id);
