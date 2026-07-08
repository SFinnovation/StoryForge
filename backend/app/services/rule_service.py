"""D&D 5e 规则服务 — 属性修正、DC 钳制、技能检定。"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from backend.app.models.models import Character

RULES_DIR = Path(__file__).resolve().parents[3] / "rules" / "dnd5e"

ABILITY_LABELS = {
    "strength": "力量",
    "dexterity": "敏捷",
    "constitution": "体质",
    "intelligence": "智力",
    "wisdom": "感知",
    "charisma": "魅力",
}

ABILITY_FROM_SHORT = {
    "str": "strength",
    "dex": "dexterity",
    "con": "constitution",
    "int": "intelligence",
    "wis": "wisdom",
    "cha": "charisma",
}

# MVP：职业 → 熟练技能
PROFESSION_SKILLS: dict[str, set[str]] = {
    "调查员": {"inv", "prc", "ins", "per"},
    "盗贼": {"ste", "acr", "itm", "prc"},
    "战士": {"ath", "itm", "prc", "sur"},
    "法师": {"arc", "his", "inv", "ins"},
}

PROFICIENCY_BONUS = 2  # MVP 1 级固定


@dataclass
class CheckOutcome:
    check_type: str
    skill_key: str | None
    attribute_used: str
    dc: int
    dice_roll: int
    ability_modifier: int
    skill_bonus: int
    final_value: int
    is_success: bool
    result_text: str


def _load_skills() -> dict:
    with open(RULES_DIR / "skills.json", encoding="utf-8") as f:
        return json.load(f)


def load_rule_file(name: str) -> dict:
    allowed = {"core", "abilities", "skills", "classes", "races", "backgrounds"}
    if name not in allowed:
        raise ValueError(f"unsupported rule file: {name}")
    with open(RULES_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def dnd5e_summary() -> dict:
    return {
        "core": load_rule_file("core"),
        "abilities": load_rule_file("abilities"),
        "skills": load_rule_file("skills")["skills"],
        "races": load_rule_file("races").get("races", []),
        "classes": load_rule_file("classes").get("classes", []),
        "backgrounds": load_rule_file("backgrounds").get("backgrounds", []),
    }


_SKILLS_DATA = _load_skills()
SKILLS = _SKILLS_DATA["skills"]


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def clamp_dc(dc: int) -> int:
    return max(5, min(30, dc))


def resolve_attribute_for_skill(skill_key: str | None, fallback_attribute: str) -> str:
    if skill_key and skill_key in SKILLS:
        short = SKILLS[skill_key]["ability"]
        return ABILITY_FROM_SHORT.get(short, fallback_attribute)
    return fallback_attribute


def get_attribute_bonus(attrs: object | None, attribute: str) -> int:
    if attrs is None:
        return 0
    score = int(getattr(attrs, attribute, 10))
    return ability_modifier(score)


def skill_bonus(character: Character, skill_key: str | None) -> int:
    if not skill_key:
        return 0
    try:
        skills = json.loads(character.skills_json or "{}")
    except json.JSONDecodeError:
        skills = {}

    skill = skills.get(skill_key)
    if isinstance(skill, dict):
        if skill.get("expertise"):
            return int(getattr(character, "proficiency_bonus", PROFICIENCY_BONUS)) * 2
        if skill.get("proficient"):
            return int(getattr(character, "proficiency_bonus", PROFICIENCY_BONUS))
    if skill is True:
        return int(getattr(character, "proficiency_bonus", PROFICIENCY_BONUS))

    profession = getattr(character, "profession", None) or getattr(character, "class_id", "")
    if skill_key in PROFESSION_SKILLS.get(profession, set()):
        return int(getattr(character, "proficiency_bonus", PROFICIENCY_BONUS))
    return 0


def format_result_text(
    *,
    dice_roll: int,
    attribute_used: str,
    ability_modifier: int,
    skill_bonus: int,
    final_value: int,
    dc: int,
    is_success: bool,
) -> str:
    attr_label = ABILITY_LABELS.get(attribute_used, attribute_used)
    skill_part = f" + 熟练(+{skill_bonus})" if skill_bonus else ""
    cmp_op = "≥" if is_success else "<"
    outcome = "成功" if is_success else "失败"
    return (
        f"d20({dice_roll}) + {attr_label}(+{ability_modifier}){skill_part} "
        f"= {final_value} {cmp_op} DC {dc}，{outcome}"
    )


def roll_check(
    character: Character,
    attrs: object | None,
    *,
    check_type: str,
    skill_key: str | None,
    attribute_used: str,
    dc: int,
) -> CheckOutcome:
    attribute = resolve_attribute_for_skill(skill_key, attribute_used)
    ability_mod = get_attribute_bonus(attrs, attribute)
    sk_bonus = skill_bonus(character, skill_key)
    dice_roll = random.randint(1, 20)
    final_value = dice_roll + ability_mod + sk_bonus
    clamped_dc = clamp_dc(dc)
    is_success = final_value >= clamped_dc
    return CheckOutcome(
        check_type=check_type,
        skill_key=skill_key,
        attribute_used=attribute,
        dc=clamped_dc,
        dice_roll=dice_roll,
        ability_modifier=ability_mod,
        skill_bonus=sk_bonus,
        final_value=final_value,
        is_success=is_success,
        result_text=format_result_text(
            dice_roll=dice_roll,
            attribute_used=attribute,
            ability_modifier=ability_mod,
            skill_bonus=sk_bonus,
            final_value=final_value,
            dc=clamped_dc,
            is_success=is_success,
        ),
    )
