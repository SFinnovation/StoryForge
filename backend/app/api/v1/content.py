"""内容导入 API — 规则书/模组 docx 提取与落库。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.api_response import success
from app.services.content_ingestion_service import ingest_module_from_docx, ingest_rulebook_from_docx
from app.services.content_pack_repository import get_adventure_module, get_rulebook_pack

router = APIRouter(prefix="/content", tags=["content"])


class DocxIngestRequest(BaseModel):
    """从本地 docx 路径导入（开发/管理端使用）。"""

    file_path: str = Field(..., description="服务器可访问的 .docx 绝对路径")
    world_id: int | None = Field(default=None, description="可选：关联到 worlds 表")
    module_title: str = Field(default="", description="模组标题（仅模组导入）")
    focus: str = Field(default="lite_dnd", description="规则书提取焦点")


@router.post("/rulebook/extract")
async def extract_rulebook(
    payload: DocxIngestRequest,
    db: Session = Depends(get_db_session),
):
    result, pack_id = await ingest_rulebook_from_docx(
        db,
        payload.file_path,
        world_id=payload.world_id,
        focus=payload.focus,
    )
    pack = get_rulebook_pack(db, pack_id)
    return success(
        {
            "pack_id": pack_id,
            "tokens_used": result.tokens_used,
            "latency_ms": result.latency_ms,
            "output": pack.model_dump() if pack else result.output.model_dump(),
        }
    )


@router.post("/module/extract")
async def extract_module(
    payload: DocxIngestRequest,
    db: Session = Depends(get_db_session),
):
    result, module_id = await ingest_module_from_docx(
        db,
        payload.file_path,
        world_id=payload.world_id,
        module_title=payload.module_title,
    )
    module = get_adventure_module(db, module_id)
    return success(
        {
            "module_id": module_id,
            "tokens_used": result.tokens_used,
            "latency_ms": result.latency_ms,
            "output": module.model_dump() if module else result.output.model_dump(),
        }
    )


@router.get("/rulebook/{pack_id}")
def get_rulebook(pack_id: int, db: Session = Depends(get_db_session)):
    pack = get_rulebook_pack(db, pack_id)
    if pack is None:
        from app.core.exceptions import StoryForgeError

        raise StoryForgeError("rulebook pack not found", status_code=404)
    return success(pack.model_dump())


@router.get("/module/{module_id}")
def get_module(module_id: int, db: Session = Depends(get_db_session)):
    module = get_adventure_module(db, module_id)
    if module is None:
        from app.core.exceptions import StoryForgeError

        raise StoryForgeError("adventure module not found", status_code=404)
    return success(module.model_dump())
