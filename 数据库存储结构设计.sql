-- ============================================================
-- AI 跑团主持助手 · 数据库建表脚本 (SQLite)
-- 基于 GD 的 10 表设计,融入审查修订:
--   [修订1] character_attributes.character_id 加 UNIQUE 强制 1:1
--   [修订2] worlds 增加 is_active 软删除(管理员下架不破坏历史外键)
--   [修订3] messages 增加 tokens_used / latency_ms(AI 工程监控图数据源)
--   [修订4] 全部枚举字段加 CHECK 约束
--   [修订5] 高频查询字段加索引
--   [修订6] 表名 sessions → game_sessions(避免与 web session 混淆)
-- 使用注意:每次建立连接后必须执行 PRAGMA foreign_keys = ON
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 1. 用户表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,              -- werkzeug.security 哈希,禁止明文
    nickname      TEXT,
    role          TEXT    NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user','admin')),
    avatar_url    TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 2. 世界观表(管理员增删改 → 权限与业务的结合点)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS worlds (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    type           TEXT    NOT NULL DEFAULT 'custom'
                   CHECK (type IN ('fantasy','mystery','scifi','custom')),
    description    TEXT    NOT NULL,             -- 给玩家看的背景介绍
    opening_prompt TEXT    NOT NULL,             -- 拼进 AI 开局提示词(AI 引擎使用)
    rule_style     TEXT,                         -- 规则风格说明,如 "轻规则 d20"
    difficulty     TEXT    NOT NULL DEFAULT 'normal'
                   CHECK (difficulty IN ('easy','normal','hard')),
    cover_url      TEXT,
    created_by     INTEGER REFERENCES users(id),
    is_public      INTEGER NOT NULL DEFAULT 1,   -- 用户自建世界观是否公开
    is_active      INTEGER NOT NULL DEFAULT 1,   -- [修订2] 软删除:0=已下架
    created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 3. 角色表
-- 说明:level/exp 为扩展预留,五天 MVP 不实现升级逻辑
--       inventory_json 用 JSON 存装备物品,MVP 不单独建物品表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS characters (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    name           TEXT    NOT NULL,
    profession     TEXT    NOT NULL,             -- 侦探/盗贼/工程师...(后端按职业映射技能加值)
    background     TEXT,
    motivation     TEXT,
    level          INTEGER NOT NULL DEFAULT 1,
    exp            INTEGER NOT NULL DEFAULT 0,
    hp             INTEGER NOT NULL DEFAULT 10,
    max_hp         INTEGER NOT NULL DEFAULT 10,
    inventory_json TEXT    NOT NULL DEFAULT '[]',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    CHECK (hp >= 0 AND hp <= max_hp)
);

-- ------------------------------------------------------------
-- 4. 角色属性表(1:1 拆表,理由:为 buff/装备临时修正等属性扩展预留)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS character_attributes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL UNIQUE          -- [修订1] UNIQUE 强制 1:1
                 REFERENCES characters(id) ON DELETE CASCADE,
    strength     INTEGER NOT NULL DEFAULT 0 CHECK (strength     BETWEEN -2 AND 5),
    dexterity    INTEGER NOT NULL DEFAULT 0 CHECK (dexterity    BETWEEN -2 AND 5),
    constitution INTEGER NOT NULL DEFAULT 0 CHECK (constitution BETWEEN -2 AND 5),
    intelligence INTEGER NOT NULL DEFAULT 0 CHECK (intelligence BETWEEN -2 AND 5),
    wisdom       INTEGER NOT NULL DEFAULT 0 CHECK (wisdom       BETWEEN -2 AND 5),
    charisma     INTEGER NOT NULL DEFAULT 0 CHECK (charisma     BETWEEN -2 AND 5)
);

-- ------------------------------------------------------------
-- 5. 跑团会话表(一局 = 一条)
-- 后端注意:创建会话时必须校验 character.user_id == 当前用户(资源归属)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS game_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    world_id      INTEGER NOT NULL REFERENCES worlds(id),
    character_id  INTEGER NOT NULL REFERENCES characters(id),
    title         TEXT,
    status        TEXT    NOT NULL DEFAULT 'playing'
                  CHECK (status IN ('playing','finished','archived')),
    current_scene TEXT,                           -- AI 维护,供上下文拼装
    current_task  TEXT,
    summary       TEXT,                           -- 简短摘要(上下文压缩用)
    started_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    ended_at      TEXT
);

-- ------------------------------------------------------------
-- 6. 剧情消息表(纯展示流;统计与查询一律走结构化表,不解析本表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    sender_type  TEXT    NOT NULL
                 CHECK (sender_type IN ('player','ai','npc','system')),
    sender_name  TEXT,
    content      TEXT    NOT NULL,
    message_type TEXT    NOT NULL DEFAULT 'narration'
                 CHECK (message_type IN ('narration','action','dialogue','dice','clue','task')),
    tokens_used  INTEGER,                         -- [修订3] 仅 AI 消息填写
    latency_ms   INTEGER,                         -- [修订3] 仅 AI 消息填写
    created_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 7. 行动判定表(判定公式:d20 + 属性修正 + 技能加值 >= DC)
-- skill_bonus 来源:后端按 characters.profession 的固定映射表给出(MVP 方案)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS action_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    message_id      INTEGER REFERENCES messages(id),   -- 关联展示流中的骰子消息
    action_text     TEXT    NOT NULL,
    check_type      TEXT    NOT NULL,             -- 调查/潜行/攻击/说服/逃跑...
    attribute_used  TEXT    NOT NULL
                    CHECK (attribute_used IN
                    ('strength','dexterity','constitution','intelligence','wisdom','charisma')),
    dc              INTEGER NOT NULL CHECK (dc BETWEEN 1 AND 30),
    dice_roll       INTEGER NOT NULL CHECK (dice_roll BETWEEN 1 AND 20),
    attribute_bonus INTEGER NOT NULL DEFAULT 0,
    skill_bonus     INTEGER NOT NULL DEFAULT 0,
    final_value     INTEGER NOT NULL,             -- = dice_roll + attribute_bonus + skill_bonus
    is_success      INTEGER NOT NULL CHECK (is_success IN (0,1)),
    result_text     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 8. 线索表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clues (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    title         TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    source_scene  TEXT,
    importance    TEXT    NOT NULL DEFAULT 'normal'
                  CHECK (importance IN ('normal','important','key')),
    discovered_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 9. 任务表(第二优先级:主流程吃紧可后接)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    title       TEXT    NOT NULL,
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'todo'
                CHECK (status IN ('todo','doing','done','failed')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- 10. 结局报告表(1:1 会话;clues_json 为归档快照,允许与 clues 表冗余)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       INTEGER NOT NULL UNIQUE
                     REFERENCES game_sessions(id) ON DELETE CASCADE,
    title            TEXT,
    story_summary    TEXT    NOT NULL,
    key_choices_json TEXT    NOT NULL DEFAULT '[]',
    clues_json       TEXT    NOT NULL DEFAULT '[]',
    ending_type      TEXT    NOT NULL DEFAULT 'open'
                     CHECK (ending_type IN ('good','normal','bad','open')),
    character_growth TEXT,
    ai_suggestion    TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- [修订5] 索引:按会话取消息/判定/线索/任务、按用户取会话与角色
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_messages_session   ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_checks_session     ON action_checks(session_id);
CREATE INDEX IF NOT EXISTS idx_checks_created     ON action_checks(created_at);
CREATE INDEX IF NOT EXISTS idx_clues_session      ON clues(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_session      ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user      ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_user    ON characters(user_id);

-- ============================================================
-- §11 AI 模块扩展表（双 Agent + Fact 分层 + 审核记录）
-- 详细设计见 docs/ai-module-design.md
-- ============================================================

-- 11.1 事实表（分层记忆，避免 NPC 全知）
CREATE TABLE IF NOT EXISTS facts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    content         TEXT    NOT NULL,
    fact_type       TEXT    NOT NULL
                    CHECK (fact_type IN (
                      'world_public','session_fact','player_known',
                      'npc_private','hidden_truth','temporary'
                    )),
    visibility_json TEXT    NOT NULL DEFAULT '{}',  -- {"player":true,"npcs":["butler_001"]}
    related_scene   TEXT,
    importance      TEXT    NOT NULL DEFAULT 'normal'
                    CHECK (importance IN ('normal','important','key')),
    status          TEXT    NOT NULL DEFAULT 'active'
                    CHECK (status IN ('locked','active','resolved')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 11.2 NPC 配置表（人格 + 知识边界）
CREATE TABLE IF NOT EXISTS npc_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    npc_id              TEXT    NOT NULL,           -- 业务 ID，如 butler_001
    name                TEXT    NOT NULL,
    personality         TEXT,
    knowledge_scope_json TEXT   NOT NULL DEFAULT '[]',
    forbidden_json      TEXT    NOT NULL DEFAULT '[]',
    speaking_style      TEXT,
    alertness           INTEGER NOT NULL DEFAULT 0 CHECK (alertness BETWEEN 0 AND 10),
    current_scene       TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (session_id, npc_id)
);

-- 11.3 NPC 记忆表（P1：观察 / 信念 / 秘密）
CREATE TABLE IF NOT EXISTS npc_memories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    npc_id          TEXT    NOT NULL,
    memory_content  TEXT    NOT NULL,
    memory_type     TEXT    NOT NULL DEFAULT 'observation'
                    CHECK (memory_type IN ('observation','belief','secret','relationship')),
    importance      TEXT    NOT NULL DEFAULT 'normal'
                    CHECK (importance IN ('normal','important','key')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 11.4 AI 审核记录表（辅 Agent 输出）
CREATE TABLE IF NOT EXISTS ai_reviews (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id           INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    message_id           INTEGER REFERENCES messages(id),
    overall_score        INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    rule_score           INTEGER CHECK (rule_score BETWEEN 0 AND 100),
    world_score          INTEGER CHECK (world_score BETWEEN 0 AND 100),
    context_score        INTEGER CHECK (context_score BETWEEN 0 AND 100),
    character_score      INTEGER CHECK (character_score BETWEEN 0 AND 100),
    npc_boundary_score   INTEGER CHECK (npc_boundary_score BETWEEN 0 AND 100),
    clue_score           INTEGER CHECK (clue_score BETWEEN 0 AND 100),
    approved             INTEGER NOT NULL CHECK (approved IN (0,1)),
    revision_count       INTEGER NOT NULL DEFAULT 0,
    used_fallback        INTEGER NOT NULL DEFAULT 0 CHECK (used_fallback IN (0,1)),
    fatal_errors_json    TEXT    NOT NULL DEFAULT '[]',
    revision_instructions_json TEXT NOT NULL DEFAULT '[]',
    created_at           TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 11.5 game_sessions 扩展字段（clue_pressure）
-- SQLite 不支持 IF NOT EXISTS 加列，部署时按需执行 ALTER：
-- ALTER TABLE game_sessions ADD COLUMN clue_pressure REAL NOT NULL DEFAULT 0.0;
-- ALTER TABLE game_sessions ADD COLUMN turns_since_key_clue INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE game_sessions ADD COLUMN failed_checks_in_scene INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_facts_session       ON facts(session_id);
CREATE INDEX IF NOT EXISTS idx_facts_type          ON facts(session_id, fact_type);
CREATE INDEX IF NOT EXISTS idx_npc_profiles_session ON npc_profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_reviews_session  ON ai_reviews(session_id);
