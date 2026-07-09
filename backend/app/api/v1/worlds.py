from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.models.models import World
from backend.app.schemas.api_response import success

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("")
def list_worlds(db: Session = Depends(get_db)):
    rows = db.query(World).filter(World.is_enabled == 1).all()
    return success(
        [
            {
                "id": w.id,
                "name": w.name,
                "type": w.type,
                "description": w.description,
                "rule_style": w.rule_style,
                "difficulty": w.difficulty,
                "cover_url": w.cover_url,
            }
            for w in rows
        ]
    )


@router.get("/{world_id}")
def get_world(world_id: int, db: Session = Depends(get_db)):
    world = db.get(World, world_id)
    if world is None or not world.is_enabled:
        from backend.app.core.exceptions import StoryForgeError

        raise StoryForgeError("world not found", status_code=404)
    return success(
        {
            "id": world.id,
            "name": world.name,
            "type": world.type,
            "description": world.description,
            "opening_prompt": world.opening_prompt,
            "rule_style": world.rule_style,
            "difficulty": world.difficulty,
        }
    )
