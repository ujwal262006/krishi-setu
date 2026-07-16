"""
AI Assistant endpoints.
RAG pipeline: query → top-5 schemes from DB → Gemini 1.5 Flash → response.
Streaming and non-streaming variants.
Anti-hallucination: only retrieved schemes are in the prompt context.
"""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import FarmerProfile
from app.routers.farmers import get_current_farmer_optional
from app.services.ai_assistant import (
    build_scheme_context,
    get_gemini_response_streamed,
    log_search,
    process_query,
    retrieve_top_schemes,
)

router = APIRouter()


# ── Request/Response schemas ───────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    response: str
    schemes_retrieved: int
    top_scheme_ids: list[int]
    response_time_ms: int


# ── Non-streaming endpoint ─────────────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse)
def ask_assistant(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_farmer: Annotated[Optional[FarmerProfile], Depends(get_current_farmer_optional)] = None,
) -> QueryResponse:
    """
    Ask the AI assistant a question about farming schemes.
    Works for both authenticated and anonymous users.
    Only schemes in the database are referenced in the response.
    """
    farmer_id = current_farmer.id if current_farmer else None
    session_id = payload.session_id or str(uuid.uuid4())

    result = process_query(
        query=payload.query,
        db=db,
        farmer_id=farmer_id,
        session_id=session_id,
    )

    return QueryResponse(**result)


# ── Streaming endpoint ─────────────────────────────────────────────────────────

@router.get("/query/stream")
async def ask_assistant_streamed(
    q: str = Query(..., min_length=1, max_length=500),
    session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Stream the AI assistant response chunk by chunk.
    Used by the frontend for real-time display.
    Query is passed as a URL parameter for SSE compatibility.
    """
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required",
        )

    import time
    start_time = time.time()

    # Retrieve schemes first
    schemes = retrieve_top_schemes(q, db, limit=5)
    scheme_context = build_scheme_context(schemes)
    top_scheme_ids = [s.id for s in schemes]

    async def generate():
        full_response = ""
        async for chunk in get_gemini_response_streamed(q, scheme_context):
            full_response += chunk
            yield chunk

        # Log after streaming completes
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_search(
            db=db,
            query_raw=q,
            query_normalized=q.lower().strip(),
            results_count=len(schemes),
            top_scheme_ids=top_scheme_ids,
            farmer_id=None,
            session_id=session_id or str(uuid.uuid4()),
            response_time_ms=elapsed_ms,
        )

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


# ── Public search (no Gemini — just scheme retrieval) ─────────────────────────

@router.get("/search")
def search_schemes_public(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict:
    """
    Public scheme search without AI response.
    Returns matching schemes directly from the database.
    Useful for frontend autocomplete and browse pages.
    """
    schemes = retrieve_top_schemes(q, db, limit=limit)
    return {
        "query": q,
        "results": [
            {
                "id": s.id,
                "name": s.name,
                "name_hindi": s.name_hindi,
                "slug": s.slug,
                "description": s.description[:200] if s.description else None,
                "application_url": s.application_url,
                "ministry_id": s.ministry_id,
            }
            for s in schemes
        ],
        "total": len(schemes),
    } 
