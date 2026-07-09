from datetime import datetime
import json

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db
from backend.app.core.exceptions import StoryForgeError
from backend.app.models.models import Character, User
from backend.app.schemas.api_response import success
from backend.app.schemas.character import CharacterCreate, CharacterResponse
from backend.app.services.auth_service import hash_password
from backend.app.services.rule_service import ability_modifier, load_rule_file

router = APIRouter(prefix="/characters", tags=["characters"])

ATTRIBUTE_NAMES = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)


def _character_response(character: Character) -> dict:
    try:
        skills = json.loads(character.skills_json or "{}")
    except json.JSONDecodeError:
        skills = {}
    try:
        saving_throws = json.loads(character.saving_throws_json or "[]")
    except json.JSONDecodeError:
        saving_throws = []
    return CharacterResponse(
        id=character.id,
        name=character.name,
        profession=character.class_id,
        class_id=character.class_id,
        race_id=character.race_id,
        background_id=character.background_id,
        motivation=character.motivation,
        level=character.level,
        exp=character.exp,
        hit_dice=character.hit_dice,
        proficiency_bonus=character.proficiency_bonus,
        hp=character.hp,
        max_hp=character.max_hp,
        attributes={
            "strength": character.strength,
            "dexterity": character.dexterity,
            "constitution": character.constitution,
            "intelligence": character.intelligence,
            "wisdom": character.wisdom,
            "charisma": character.charisma,
        },
        skills=skills,
        saving_throws=saving_throws,
    ).model_dump()


def _attrs_to_dict(payload: CharacterCreate) -> dict[str, int]:
    attrs = payload.base_attributes or payload.attributes
    return {name: int(getattr(attrs, name)) for name in ATTRIBUTE_NAMES}


def _find_by_id(items: list[dict], item_id: str | None) -> dict | None:
    if not item_id:
        return None
    return next((item for item in items if item.get("id") == item_id), None)


def _hit_dice_max(hit_dice: str | None) -> int:
    if not hit_dice or not hit_dice.startswith("d"):
        return 8
    try:
        return int(hit_dice[1:])
    except ValueError:
        return 8


def _selected_skill_keys(payload: CharacterCreate) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for skill in payload.selected_skills:
        if skill not in seen:
            seen.add(skill)
            result.append(skill)
    return result


def _build_character_rules(payload: CharacterCreate) -> dict:
    attrs = _attrs_to_dict(payload)
    core = load_rule_file("core")
    skills_rule = load_rule_file("skills")["skills"]
    classes = load_rule_file("classes").get("classes", [])
    races = load_rule_file("races").get("races", [])
    backgrounds = load_rule_file("backgrounds").get("backgrounds", [])

    if payload.ability_assignment == "standard_array":
        expected = sorted(core.get("standard_array", []))
        actual = sorted(attrs.values())
        if actual != expected:
            raise StoryForgeError("base_attributes must match D&D 5e standard array", status_code=422)

    class_id = payload.class_id or payload.profession
    cls = _find_by_id(classes, class_id)
    if payload.class_id and cls is None:
        raise StoryForgeError("invalid class_id", status_code=422)

    race = _find_by_id(races, payload.race_id)
    if payload.race_id and race is None:
        raise StoryForgeError("invalid race_id", status_code=422)

    background = _find_by_id(backgrounds, payload.background_id)
    if payload.background_id and background is None:
        raise StoryForgeError("invalid background_id", status_code=422)

    if race:
        for attr, bonus in race.get("ability_increases", {}).items():
            if attr in attrs:
                attrs[attr] = min(int(core.get("max_ability_score", 20)), attrs[attr] + int(bonus))

    selected_skills = _selected_skill_keys(payload)
    invalid_skills = [skill for skill in selected_skills if skill not in skills_rule]
    if invalid_skills:
        raise StoryForgeError(f"invalid selected_skills: {', '.join(invalid_skills)}", status_code=422)

    class_skill_choices = (cls or {}).get("skill_choices", [])
    if class_skill_choices and selected_skills:
        first_choice = class_skill_choices[0]
        allowed = set(first_choice.get("from", []))
        choose_count = int(first_choice.get("choose", len(selected_skills)))
        if "*" not in allowed and not set(selected_skills).issubset(allowed):
            raise StoryForgeError("selected_skills contain skills not allowed by class", status_code=422)
        if len(selected_skills) > choose_count:
            raise StoryForgeError("too many selected_skills for class", status_code=422)

    proficient_skills = set(selected_skills)
    for source in ((race or {}).get("skill_proficiencies", []), (background or {}).get("skill_proficiencies", [])):
        for skill in source:
            if isinstance(skill, str) and skill in skills_rule:
                proficient_skills.add(skill)

    skills_json = {skill: {"proficient": True} for skill in sorted(proficient_skills)}
    saving_throws = (cls or {}).get("saving_throws", [])
    hit_dice = (cls or {}).get("hit_dice", "d8")
    max_hp = max(1, _hit_dice_max(hit_dice) + ability_modifier(attrs["constitution"]))

    return {
        "class_id": class_id,
        "attrs": attrs,
        "max_hp": max_hp,
        "hit_dice": hit_dice,
        "skills_json": skills_json,
        "saving_throws": saving_throws,
    }


def _ensure_user(db: Session, user_id: int) -> None:
    if db.get(User, user_id) is not None:
        return
    db.add(
        User(
            id=user_id,
            username=f"demo_user_{user_id}",
            password_hash=hash_password("demo"),
            nickname="Demo User",
            role="user",
            status="active",
            is_temporary=0,
        )
    )
    db.flush()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_character(
    payload: CharacterCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    derived = _build_character_rules(payload)
    attrs = derived["attrs"]
    max_hp = derived["max_hp"] if payload.base_attributes or payload.class_id else payload.max_hp
    hp = max_hp if payload.base_attributes or payload.class_id else payload.hp
    if max_hp < hp:
        raise StoryForgeError("max_hp must be greater than or equal to hp", status_code=422)

    character = Character(
        user_id=user_id,
        name=payload.name,
        race_id=payload.race_id,
        class_id=derived["class_id"],
        background_id=payload.background_id,
        motivation=payload.motivation,
        level=1,
        exp=0,
        hp=hp,
        max_hp=max_hp,
        hit_dice=derived["hit_dice"],
        proficiency_bonus=2,
        strength=attrs["strength"],
        dexterity=attrs["dexterity"],
        constitution=attrs["constitution"],
        intelligence=attrs["intelligence"],
        wisdom=attrs["wisdom"],
        charisma=attrs["charisma"],
        skills_json=json.dumps(derived["skills_json"], ensure_ascii=False),
        saving_throws_json=json.dumps(derived["saving_throws"], ensure_ascii=False),
        inventory_json="[]",
        created_at=datetime.utcnow(),
    )
    try:
        _ensure_user(db, user_id)
        db.add(character)
        db.flush()
        db.commit()
        db.refresh(character)
    except Exception:
        db.rollback()
        raise
    return success(_character_response(character), message="character created")


@router.get("")
def list_characters(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    rows = db.query(Character).filter(Character.user_id == user_id).all()
    return success([_character_response(c) for c in rows])


@router.get("/{character_id}")
def get_character(
    character_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != user_id:
        raise StoryForgeError("character not found", status_code=404)
    return success(_character_response(character))
