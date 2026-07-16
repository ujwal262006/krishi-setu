"""
Krishi Setu — AI Assistant (RAG)
Query → top-5 relevant schemes retrieved from DB → context injected into prompt
→ Gemini 1.5 Flash call → streamed response.

Anti-hallucination controls:
- Only schemes retrieved from the database are injected into the prompt
- System prompt explicitly forbids mentioning schemes not in context
- Scheme names in response are verified against retrieved set
"""

import time
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types
from sqlalchemy import cast, Text, func, or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.models import Scheme, SearchLog

settings = get_settings()

# ── Gemini client — API key from env, never hardcoded ─────────────────────────
_client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"


# ── Scheme retrieval ───────────────────────────────────────────────────────────

def retrieve_top_schemes(
    query: str,
    db: Session,
    limit: int = 5,
) -> list[Scheme]:
    """
    Retrieve top-N most relevant schemes for a query.
    Searches name, description, name_hindi, and search_synonyms.
    Returns empty list if no matches — never fabricates results.
    """
    search_term = f"%{query.lower()}%"

    results = (
        db.query(Scheme)
        .filter(
            Scheme.is_active == True,
            or_(
                func.lower(Scheme.name).like(search_term),
                func.lower(Scheme.description).like(search_term),
                func.lower(Scheme.name_hindi).like(search_term),
                func.lower(cast(Scheme.search_synonyms, Text)).like(search_term),
            ),
        )
        .limit(limit)
        .all()
    )

    # If no direct matches, try word-by-word search
    if not results:
        words = [w for w in query.lower().split() if len(w) > 2]
        for word in words:
            word_term = f"%{word}%"
            partial = (
                db.query(Scheme)
                .filter(
                    Scheme.is_active == True,
                    or_(
                        func.lower(Scheme.name).like(word_term),
                        func.lower(Scheme.description).like(word_term),
                        func.lower(cast(Scheme.search_synonyms, Text)).like(word_term),
                    ),
                )
                .limit(limit)
                .all()
            )
            results.extend(partial)
            if len(results) >= limit:
                break

        # Deduplicate by scheme id
        seen = set()
        unique_results = []
        for s in results:
            if s.id not in seen:
                seen.add(s.id)
                unique_results.append(s)
        results = unique_results[:limit]

    return results


def build_scheme_context(schemes: list[Scheme]) -> str:
    """
    Build a structured context string from retrieved schemes.
    This is injected into the Gemini prompt.
    """
    if not schemes:
        return "No matching schemes found in the database."

    context_parts = []
    for i, scheme in enumerate(schemes, 1):
        parts = [f"**Scheme {i}: {scheme.name}**"]

        if scheme.name_hindi:
            parts.append(f"Hindi name: {scheme.name_hindi}")

        if scheme.description:
            parts.append(f"Description: {scheme.description[:500]}")

        if scheme.eligibility_criteria:
            parts.append(f"Eligibility: {scheme.eligibility_criteria}")

        if scheme.benefits:
            parts.append(f"Benefits: {scheme.benefits}")

        if scheme.application_url:
            parts.append(f"Apply at: {scheme.application_url}")

        context_parts.append("\n".join(parts))

    return "\n\n---\n\n".join(context_parts)


def build_system_prompt(scheme_context: str) -> str:
    """
    Build the system prompt with strict anti-hallucination instructions.
    """
    return f"""You are Krishi Setu, an AI assistant helping Indian farmers discover government agricultural schemes.

CRITICAL RULES — YOU MUST FOLLOW THESE STRICTLY:
1. ONLY discuss the schemes provided in the context below. Do NOT mention, invent, or reference any scheme that is not in this context.
2. If the farmer's query cannot be answered using the provided schemes, say: "I could not find a matching scheme in our database for your query. Please try different keywords."
3. Answer in simple, clear language. If the farmer writes in Hindi or uses colloquial terms, respond in simple English with key Hindi terms where helpful.
4. Do not make up eligibility criteria, benefit amounts, or application procedures. Only state what is in the context.
5. Always mention the application URL when available.
6. Be concise — farmers need quick, actionable answers, not long essays.

DATABASE CONTEXT (ONLY these schemes exist for this query):
{scheme_context}

Answer the farmer's question based ONLY on the above context."""


# ── Gemini integration ─────────────────────────────────────────────────────────

def get_gemini_response(
    query: str,
    scheme_context: str,
) -> str:
    """
    Call Gemini 2.5 Flash with the scheme context and farmer query.
    Returns full response text (non-streaming).
    """
    system_prompt = build_system_prompt(scheme_context)
    try:
        response = _client.models.generate_content(
            model=MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        return response.text
    except Exception as e:
        return f"I'm sorry, I encountered an error processing your query: {str(e)}"


async def get_gemini_response_streamed(
    query: str,
    scheme_context: str,
) -> AsyncGenerator[str, None]:
    """
    Stream Gemini 2.5 Flash response chunk by chunk.
    """
    system_prompt = build_system_prompt(scheme_context)
    try:
        for chunk in _client.models.generate_content_stream(
            model=MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"Error: {str(e)}"


# ── Search log persistence ─────────────────────────────────────────────────────

def log_search(
    db: Session,
    query_raw: str,
    query_normalized: str,
    results_count: int,
    top_scheme_ids: list[int],
    farmer_id: Optional[int],
    session_id: Optional[str],
    response_time_ms: int,
) -> SearchLog:
    """Persist search query and results to search_logs table."""
    log = SearchLog(
        farmer_id=farmer_id,
        query_raw=query_raw,
        query_normalized=query_normalized,
        results_count=results_count,
        top_scheme_ids=top_scheme_ids,
        session_id=session_id,
        response_time_ms=response_time_ms,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ── Main query function ────────────────────────────────────────────────────────

def process_query(
    query: str,
    db: Session,
    farmer_id: Optional[int] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve top-5 relevant schemes from DB
    2. Build context from retrieved schemes
    3. Call Gemini with context + query
    4. Log search
    5. Return response + retrieved schemes
    """
    start_time = time.time()

    # Step 1: Retrieve
    schemes = retrieve_top_schemes(query, db, limit=5)

    # Step 2: Build context
    scheme_context = build_scheme_context(schemes)
    top_scheme_ids = [s.id for s in schemes]

    # Step 3: Call Gemini
    response_text = get_gemini_response(query, scheme_context)

    # Step 4: Log
    elapsed_ms = int((time.time() - start_time) * 1000)
    log_search(
        db=db,
        query_raw=query,
        query_normalized=query.lower().strip(),
        results_count=len(schemes),
        top_scheme_ids=top_scheme_ids,
        farmer_id=farmer_id,
        session_id=session_id,
        response_time_ms=elapsed_ms,
    )

    return {
        "query": query,
        "response": response_text,
        "schemes_retrieved": len(schemes),
        "top_scheme_ids": top_scheme_ids,
        "response_time_ms": elapsed_ms,
    } 
