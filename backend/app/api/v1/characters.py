from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.models.models import Character
from backend.app.schemas.api_response import success

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
                "profession": c.class_id,
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
        from backend.app.core.exceptions import StoryForgeError

        raise StoryForgeError("character not found", status_code=404)
    return success(
        {
            "id": character.id,
            "name": character.name,
            "profession": character.class_id,
            "background": character.background_id,
            "motivation": character.motivation,
            "attributes": {
                "strength": character.strength,
                "dexterity": character.dexterity,
                "constitution": character.constitution,
                "intelligence": character.intelligence,
                "wisdom": character.wisdom,
                "charisma": character.charisma,
            },
        }
    )
