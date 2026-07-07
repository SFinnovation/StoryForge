#!/usr/bin/env python3
"""
从 Foundry VTT dnd5e 6.0.x 数据包提取 StoryForge 可用的规则 JSON。
数据来源：dnd5e-6.0.x/dnd5e-6.0.x/（SRD 5.1 / CC-BY-4.0）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("请先安装 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DND_ROOT = ROOT / "dnd5e-6.0.x" / "dnd5e-6.0.x"
OUT_DIR = ROOT / "rules" / "dnd5e"

# 与 dnd5e module/config.mjs 对齐的核心规则
CORE_RULES = {
    "source": "Foundry VTT dnd5e 6.0.x (SRD 5.1, CC-BY-4.0)",
    "max_level": 20,
    "max_ability_score": 20,
    "ability_modifier_formula": "floor((score - 10) / 2)",
    "standard_array": [15, 14, 13, 12, 10, 8],
    "point_buy": {"total_points": 27, "min_score": 8, "max_score_before_racial": 15},
    "proficiency_bonus_by_level": {
        str(i): 2 + (i - 1) // 4 for i in range(1, 21)
    },
    "character_exp_levels": [
        0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
        85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000,
    ],
    "dc_by_difficulty": {
        "very_easy": 5,
        "easy": 10,
        "medium": 15,
        "hard": 20,
        "very_hard": 25,
        "nearly_impossible": 30,
    },
    "check_formula": "d20 + ability_modifier + proficiency_bonus + other >= dc",
    "passive_score_base": 10,
    "advantage_disadvantage_passive_modifier": 5,
    "default_abilities": {
        "melee_attack": "strength",
        "ranged_attack": "dexterity",
        "initiative": "dexterity",
        "hit_points": "constitution",
        "concentration": "constitution",
    },
    "proficiency_levels": {
        "0": "none",
        "0.5": "half",
        "1": "proficient",
        "2": "expertise",
    },
}

ABILITIES = {
    "str": {"key": "strength", "label_zh": "力量", "label_en": "Strength", "type": "physical"},
    "dex": {"key": "dexterity", "label_zh": "敏捷", "label_en": "Dexterity", "type": "physical"},
    "con": {"key": "constitution", "label_zh": "体质", "label_en": "Constitution", "type": "physical"},
    "int": {"key": "intelligence", "label_zh": "智力", "label_en": "Intelligence", "type": "mental"},
    "wis": {"key": "wisdom", "label_zh": "感知", "label_en": "Wisdom", "type": "mental"},
    "cha": {"key": "charisma", "label_zh": "魅力", "label_en": "Charisma", "type": "mental"},
}

SKILLS = {
    "acr": {"key": "acrobatics", "label_zh": "杂技", "label_en": "Acrobatics", "ability": "dex"},
    "ani": {"key": "animal_handling", "label_zh": "驯兽", "label_en": "Animal Handling", "ability": "wis"},
    "arc": {"key": "arcana", "label_zh": "奥秘", "label_en": "Arcana", "ability": "int"},
    "ath": {"key": "athletics", "label_zh": "运动", "label_en": "Athletics", "ability": "str"},
    "dec": {"key": "deception", "label_zh": "欺瞒", "label_en": "Deception", "ability": "cha"},
    "his": {"key": "history", "label_zh": "历史", "label_en": "History", "ability": "int"},
    "ins": {"key": "insight", "label_zh": "洞悉", "label_en": "Insight", "ability": "wis"},
    "itm": {"key": "intimidation", "label_zh": "威吓", "label_en": "Intimidation", "ability": "cha"},
    "inv": {"key": "investigation", "label_zh": "调查", "label_en": "Investigation", "ability": "int"},
    "med": {"key": "medicine", "label_zh": "医药", "label_en": "Medicine", "ability": "wis"},
    "nat": {"key": "nature", "label_zh": "自然", "label_en": "Nature", "ability": "int"},
    "prc": {"key": "perception", "label_zh": "察觉", "label_en": "Perception", "ability": "wis"},
    "prf": {"key": "performance", "label_zh": "表演", "label_en": "Performance", "ability": "cha"},
    "per": {"key": "persuasion", "label_zh": "说服", "label_en": "Persuasion", "ability": "cha"},
    "rel": {"key": "religion", "label_zh": "宗教", "label_en": "Religion", "ability": "int"},
    "slt": {"key": "sleight_of_hand", "label_zh": "巧手", "label_en": "Sleight of Hand", "ability": "dex"},
    "ste": {"key": "stealth", "label_zh": "隐匿", "label_en": "Stealth", "ability": "dex"},
    "sur": {"key": "survival", "label_zh": "生存", "label_en": "Survival", "ability": "wis"},
}

SKILL_ALIASES = {
    "潜行": "ste", "stealth": "ste",
    "调查": "inv", "investigation": "inv",
    "察觉": "prc", "perception": "prc",
    "说服": "per", "persuasion": "per",
    "欺瞒": "dec", "deception": "dec",
    "威吓": "itm", "intimidation": "itm",
    "运动": "ath", "athletics": "ath",
    "杂技": "acr", "acrobatics": "acr",
    "隐匿": "ste",
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def strip_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).replace("\n", " ").strip()


def parse_ability_increases(advancement: list) -> dict[str, int]:
    result: dict[str, int] = {}
    for step in advancement or []:
        if step.get("type") != "AbilityScoreImprovement":
            continue
        fixed = step.get("configuration", {}).get("fixed", {})
        for abbr, val in fixed.items():
            if val and abbr in ABILITIES:
                result[ABILITIES[abbr]["key"]] = result.get(ABILITIES[abbr]["key"], 0) + int(val)
    return result


def parse_trait_grants(advancement: list) -> dict:
    skills: list[str] = []
    saves: list[str] = []
    languages: dict = {"grants": [], "choices": 0}
    for step in advancement or []:
        if step.get("type") != "Trait":
            continue
        cfg = step.get("configuration", {})
        for grant in cfg.get("grants", []) or []:
            if grant.startswith("skills:"):
                skills.append(grant.split(":", 1)[1])
            elif grant.startswith("saves:"):
                saves.append(ABILITIES.get(grant.split(":", 1)[1], {}).get("key", grant))
            elif grant.startswith("languages:"):
                languages["grants"].append(grant)
        for choice in cfg.get("choices", []) or []:
            pool = choice.get("pool", [])
            count = choice.get("count", 0)
            if any(str(p).startswith("skills:") for p in pool):
                # 职业/背景技能选择池
                skills.append({"choose": count, "from": [p.split(":", 1)[1] for p in pool if str(p).startswith("skills:")]})
            elif any(str(p).startswith("languages:") for p in pool):
                languages["choices"] += count
    return {"skill_proficiencies": skills, "saving_throw_proficiencies": saves, "languages": languages}


def extract_classes() -> list[dict]:
    classes_dir = DND_ROOT / "packs" / "_source" / "classes"
    items = []
    for path in sorted(classes_dir.glob("*.yml")):
        data = load_yaml(path)
        sys_data = data.get("system", {})
        traits = parse_trait_grants(sys_data.get("advancement", []))
        items.append({
            "id": sys_data.get("identifier") or path.stem,
            "name_en": data.get("name"),
            "name_zh": data.get("name"),  # 可后续人工翻译
            "hit_dice": sys_data.get("hitDice", "d8"),
            "primary_abilities": sys_data.get("primaryAbility", {}),
            "saving_throws": traits["saving_throw_proficiencies"],
            "skill_choices": traits["skill_proficiencies"],
            "spellcasting": sys_data.get("spellcasting", {}),
            "description_text": strip_html(sys_data.get("description", {}).get("value", ""))[:500],
        })
    return items


def extract_races() -> list[dict]:
    races_dir = DND_ROOT / "packs" / "_source" / "races"
    items = []
    for path in sorted(races_dir.rglob("*.yml")):
        if path.name == "_folder.yml" or "-features" in str(path):
            continue
        data = load_yaml(path)
        if data.get("type") != "race":
            continue
        sys_data = data.get("system", {})
        traits = parse_trait_grants(sys_data.get("advancement", []))
        items.append({
            "id": sys_data.get("identifier") or path.stem,
            "name_en": data.get("name"),
            "name_zh": data.get("name"),
            "ability_increases": parse_ability_increases(sys_data.get("advancement", [])),
            "speed": sys_data.get("movement", {}).get("walk", 30),
            "size": "medium",
            "skill_proficiencies": traits["skill_proficiencies"],
            "languages": traits["languages"],
            "description_text": strip_html(sys_data.get("description", {}).get("value", ""))[:400],
        })
    return items


def extract_backgrounds() -> list[dict]:
    bg_dir = DND_ROOT / "packs" / "_source" / "backgrounds"
    items = []
    for path in sorted(bg_dir.glob("*.yml")):
        data = load_yaml(path)
        sys_data = data.get("system", {})
        traits = parse_trait_grants(sys_data.get("advancement", []))
        items.append({
            "id": sys_data.get("identifier") or path.stem,
            "name_en": data.get("name"),
            "name_zh": data.get("name"),
            "skill_proficiencies": traits["skill_proficiencies"],
            "languages": traits["languages"],
            "description_text": strip_html(sys_data.get("description", {}).get("value", ""))[:400],
        })
    return items


def write_json(name: str, data) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    if not DND_ROOT.exists():
        print(f"未找到 dnd5e 数据包: {DND_ROOT}", file=sys.stderr)
        sys.exit(1)

    print("Extracting D&D 5e rules for StoryForge...")
    write_json("core.json", CORE_RULES)
    write_json("abilities.json", ABILITIES)
    write_json("skills.json", {"skills": SKILLS, "aliases": SKILL_ALIASES})
    write_json("classes.json", {"classes": extract_classes()})
    write_json("races.json", {"races": extract_races()})
    write_json("backgrounds.json", {"backgrounds": extract_backgrounds()})
    print("Done.")


if __name__ == "__main__":
    main()
