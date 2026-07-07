from fastapi import FastAPI

from app.api import actions
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="StoryForge API — 故事创作与管理平台",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
