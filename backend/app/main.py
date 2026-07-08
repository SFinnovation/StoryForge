from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.ai.services.llm_client import close_llm_client, init_llm_client
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import StoryForgeError
from app.db.init_db import init_db
from app.schemas.api_response import error


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await init_llm_client()
    yield
    await close_llm_client()


app = FastAPI(
    title=settings.APP_NAME,
    description="StoryForge API — 故事创作与管理平台",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(StoryForgeError)
async def storyforge_error_handler(request: Request, exc: StoryForgeError):
    code_map = {
        404: 40401,
        403: 40301,
        409: 40901,
        422: 42201,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error(code_map.get(exc.status_code, 50001), exc.message).model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
