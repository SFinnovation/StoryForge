from fastapi import APIRouter

from backend.app.api.v1 import (
    auth,
    chapters,
    characters,
    content,
    export,
    rules,
    sessions,
    stories,
    worldbuilding,
    worlds,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(rules.router)
api_router.include_router(sessions.router)
api_router.include_router(worlds.router)
api_router.include_router(characters.router)
api_router.include_router(content.router)
api_router.include_router(stories.router)
api_router.include_router(chapters.router)
api_router.include_router(worldbuilding.router)
api_router.include_router(export.router)
