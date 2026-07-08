from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_id, get_db_session
from backend.app.models.models import Character, World
from backend.app.schemas.api_response import success

router = APIRouter(tags=["worlds"])


@router.get("/worlds")
def list_worlds(db: Session = Depends(get_db_session)):
    rows = db.query(World).filter(World.is_active == 1).all()
    return success(
        [
            {
                "id": w.id,
                "name": w.name,
                "type": w.type,
                "description": w.description,
                "difficulty": w.difficulty,
                "cover_url": w.cover_url,
            }
            for w in rows
        ]
    )


@router.get("/worlds/{world_id}")
def get_world(world_id: int, db: Session = Depends(get_db_session)):
    world = db.get(World, world_id)
    if world is None or not world.is_active:
        from backend.app.core.exceptions import StoryForgeError

        raise StoryForgeError("world not found", status_code=404)
    return success(
        {
            "id": world.id,
            "name": world.name,
            "type": world.type,
            "description": world.description,
            "opening_prompt": world.opening_prompt,
            "difficulty": world.difficulty,
        }
    )
