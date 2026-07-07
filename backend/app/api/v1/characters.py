from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db_session
from app.models.game import Character, CharacterAttributes
from app.schemas.api_response import success

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
def list_characters(
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    rows = db.query(Character).filter(Character.user_id == user_id).all()
    return success(
        [
            {
                "id": c.id,
                "name": c.name,
                "profession": c.profession,
                "motivation": c.motivation,
                "hp": c.hp,
                "max_hp": c.max_hp,
            }
            for c in rows
        ]
    )


@router.get("/{character_id}")
def get_character(
    character_id: int,
    db: Session = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != user_id:
        from app.core.exceptions import StoryForgeError

        raise StoryForgeError("character not found", status_code=404)
    attrs = (
        db.query(CharacterAttributes)
        .filter(CharacterAttributes.character_id == character.id)
        .first()
    )
    return success(
        {
            "id": character.id,
            "name": character.name,
            "profession": character.profession,
            "background": character.background,
            "motivation": character.motivation,
            "attributes": {
                "strength": attrs.strength if attrs else 0,
                "dexterity": attrs.dexterity if attrs else 0,
                "constitution": attrs.constitution if attrs else 0,
                "intelligence": attrs.intelligence if attrs else 0,
                "wisdom": attrs.wisdom if attrs else 0,
                "charisma": attrs.charisma if attrs else 0,
            },
        }
    )
