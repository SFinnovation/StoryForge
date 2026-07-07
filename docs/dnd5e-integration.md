# D&D 5e 规则整合说明

> 数据来源：[Foundry VTT dnd5e 6.0.x](https://github.com/foundryvtt/dnd5e)（SRD 5.1，CC-BY-4.0）  
> 机器可读规则：`rules/dnd5e/*.json`  
> 提取脚本：`scripts/extract_dnd5e_rules.py`

---

## 1. 整合策略

StoryForge **不运行 Foundry**，只借用其结构化 SRD 数据，在后端实现轻量规则引擎：

| 层级 | 做法 |
|------|------|
| **P0 MVP** | 六大属性、d20 检定、熟练加值、18 项技能映射、种族/职业/背景选择、HP 计算 |
| **P1** | 豁免检定、优势/劣势、被动察觉、经验升级 |
| **P2** | 完整战斗轮、法术位、装备 AC |

原则：**数值与掷骰在后端，叙事在 AI**。

---

## 2. 规则数据文件

```
rules/dnd5e/
├── core.json          # 核心公式、熟练加值表、DC 表、XP 表
├── abilities.json     # 六大属性
├── skills.json        # 18 技能 + 中文别名（供 AI 映射）
├── classes.json       # 12 职业（生命骰、豁免、技能池）
├── races.json         # 9 种族（属性加值、速度、语言）
└── backgrounds.json   # 背景（技能熟练、语言）
```

重新提取（更新 dnd5e 包后）：

```bash
pip install pyyaml
python scripts/extract_dnd5e_rules.py
```

---

## 3. 角色创建流程（D&D 5e）

```
1. 选择种族 race_id     → 应用 ability_increases
2. 选择职业 class_id    → 确定 hit_dice、豁免熟练、技能选择池
3. 选择背景 background_id → 追加技能熟练、语言
4. 分配基础属性         → 标准数组 或 27 点购买（后端校验）
5. 选择职业技能         → 从 skill_choices 中选取 N 项
6. 计算衍生数值         → modifier、proficiency_bonus、max_hp
```

### 3.1 属性加值顺序

```
base_scores（玩家分配）
  → + racial ability_increases
  → 上限 20（MVP 1 级角色）
  → 计算 modifiers
```

### 3.2 生命值（1 级）

```
max_hp = hit_dice_max + constitution_modifier

示例：游荡者 d8，体质 14（+2）→ max_hp = 8 + 2 = 10
```

`hit_dice_max` 来自 `classes.json` 中职业的 `hit_dice` 字段（如 `d8` → 8）。

### 3.3 熟练加值（1 级）

```
proficiency_bonus = 2   # 见 core.json proficiency_bonus_by_level
```

---

## 4. 检定公式（整合后）

### 4.1 属性检定 / 技能检定

```
total = d20 + ability_modifier + skill_bonus

skill_bonus =
  0                          # 未熟练
  proficiency_bonus          # 熟练
  proficiency_bonus * 2      # 专精（游荡者 Expertise，P1）
```

技能使用的属性由 `skills.json` 的 `ability` 字段决定（如隐匿 `ste` → 敏捷）。

### 4.2 豁免检定（P1）

```
total = d20 + ability_modifier + (proficiency_bonus if save_proficient else 0)
```

豁免熟练来自职业 `saving_throws`（如游荡者：敏捷、智力）。

### 4.3 攻击检定（P2）

```
total = d20 + ability_modifier + proficiency_bonus   # 熟练武器/法术攻击
命中条件：total >= target_ac
```

### 4.4 DC 参考（SRD）

| 难度 | DC |
|------|-----|
| 非常容易 | 5 |
| 简单 | 10 |
| 中等 | 15 |
| 困难 | 20 |
| 非常困难 | 25 |
| 几乎不可能 | 30 |

AI 建议 DC 后，后端钳制到 `[5, 30]`。

---

## 5. 行动理解 → 规则映射

AI 在 `action_parse` 阶段输出：

```json
{
  "skill_key": "ste",
  "attribute_used": "dexterity",
  "suggested_dc": 15,
  "needs_check": true
}
```

后端 `rule_service.resolve_check()` 流程：

```
1. skill_key → skills.json 查默认属性
2. 读取角色 skill 熟练状态（skills_json）
3. 计算 ability_modifier + skill_bonus
4. dice_service.roll_d20()
5. 判定 success / failure
```

### 5.1 技能别名

`skills.json` 的 `aliases` 支持中英文与 fullKey，例如：

- `潜行` / `stealth` → `ste`
- `调查` / `investigation` → `inv`

---

## 6. 数据库字段扩展

在 `characters` 表增加 D&D 字段（见 implementation-spec §6）：

| 字段 | 说明 |
|------|------|
| `race_id` | 如 `high-elf` |
| `class_id` | 如 `rogue` |
| `background_id` | 如 `acolyte` |
| `skills_json` | `{"ste":{"proficient":true},"inv":{"proficient":true}}` |
| `saving_throws_json` | `["dexterity","intelligence"]` |
| `proficiency_bonus` | 当前熟练加值，默认 2 |
| `hit_dice` | 如 `d8` |

---

## 7. API 扩展

### GET `/api/rules/dnd5e/summary`

返回前端角色创建所需的 races / classes / backgrounds 列表（从 JSON 读取）。

### POST `/api/characters` 请求扩展

```json
{
  "name": "艾琳",
  "race_id": "high-elf",
  "class_id": "rogue",
  "background_id": "acolyte",
  "motivation": "寻找失踪的导师",
  "ability_assignment": "standard_array",
  "base_attributes": {
    "strength": 8, "dexterity": 15, "constitution": 12,
    "intelligence": 14, "wisdom": 13, "charisma": 10
  },
  "selected_skills": ["ste", "inv", "prc", "ins"]
}
```

后端校验：
- `selected_skills` 数量符合职业 `skill_choices`
- 背景技能自动合并
- 种族加值后属性 ≤ 20

---

## 8. MVP 与完整规则边界

| 规则 | MVP | 说明 |
|------|-----|------|
| 六大属性 + 修正 | ✅ | SRD 标准 |
| 18 项技能 | ✅ | 含熟练加值 |
| 12 职业 + 9 种族 | ✅ | 来自 JSON |
| 1 背景（侍僧） | ✅ | 可扩展 |
| 生命骰 / HP | ✅ | 仅 1 级 |
| 豁免检定 | P1 | 数据结构已预留 |
| 优势 / 劣势 | P1 | 掷双 d20 取高/低 |
| 法术与法术位 | P2 | classes 含 spellcasting 元数据 |
| 完整装备 / AC | P2 | Foundry 物品包不导入 |

---

## 9. 许可说明

- **SRD 5.1 内容**：CC-BY-4.0，需在项目中注明来源  
- **Foundry dnd5e 代码**：MIT（我们仅参考数据结构与公式，不嵌入其 JS 运行时）  
- **StoryForge 整合层**：项目自有 MIT 许可

建议在 README 或关于页注明：

> 本项目游戏规则基于 D&D 5e SRD，部分数据来源于 Foundry VTT dnd5e 系统（CC-BY-4.0 / MIT）。

---

## 10. 参考对照

| StoryForge 模块 | dnd5e 来源 |
|-----------------|------------|
| `rule_service` | `module/config.mjs`（abilities, skills, DC, XP） |
| `dice_service` | SRD d20 检定 |
| `rules/dnd5e/classes.json` | `packs/_source/classes/*.yml` |
| `rules/dnd5e/races.json` | `packs/_source/races/**/*.yml` |
| `rules/dnd5e/backgrounds.json` | `packs/_source/backgrounds/*.yml` |
