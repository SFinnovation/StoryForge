from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.ai.services.llm_client import close_llm_client, init_llm_client
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.exceptions import StoryForgeError
from backend.app.db.init_db import init_db, seed_demo_data
from backend.app.schemas.api_response import error


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DB_AUTO_CREATE:
        init_db()
    if settings.SEED_DEMO_DATA:
        seed_demo_data()
    await init_llm_client()
    yield
    await close_llm_client()


app = FastAPI(
    title=settings.APP_NAME,
    description="StoryForge API — 故事创作与管理平台",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
