from fastapi import APIRouter

from backend.app.schemas.api_response import success
from backend.app.services.rule_service import dnd5e_summary, load_rule_file

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/dnd5e/summary")
def get_dnd5e_summary():
    return success(dnd5e_summary())


@router.get("/dnd5e/skills")
def get_dnd5e_skills():
    data = load_rule_file("skills")
    return success(data)
