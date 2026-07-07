from fastapi import APIRouter

from app.api.v1 import chapters, export, stories, worldbuilding

api_router = APIRouter()

api_router.include_router(stories.router)
api_router.include_router(chapters.router)
api_router.include_router(worldbuilding.router)
api_router.include_router(export.router)
