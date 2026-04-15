"""Routes for local RAG inspection."""

from fastapi import APIRouter, Request

from app.models import RagSearchRequest, RagSearchResponse, RagStatusResponse
from app.services.rag_service import get_rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/status", response_model=RagStatusResponse)
async def rag_status(request: Request):
    service = get_rag_service()
    return RagStatusResponse(**service.status())


@router.post("/search", response_model=RagSearchResponse)
async def rag_search(payload: RagSearchRequest, request: Request):
    service = get_rag_service()
    result = service.search(payload.question, top_k=payload.top_k)
    return RagSearchResponse(
        question=result.question,
        context=result.context,
        sources=result.sources,
        enabled=result.enabled,
        indexed_files=result.indexed_files,
        indexed_chunks=result.indexed_chunks,
        corpus_path=result.corpus_path,
    )
