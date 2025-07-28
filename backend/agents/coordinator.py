from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import uuid
import httpx

from utils.mcp import build_mcp_message
from utils.logger import log_trace

router = APIRouter()

INGESTION_URL = "http://localhost:8000/agent/ingestion/parse"
RETRIEVAL_URL = "http://localhost:8000/agent/retrieval/retrieve"
LLM_URL = "http://localhost:8000/agent/llm/respond"


@router.post("/start")
async def coordinator_handler(
    files: List[UploadFile] = File(...),
    user_query: str = Form(...)
):
    trace_id = f"trace-{str(uuid.uuid4())[:8]}"
    log_trace("Received user query and documents", trace_id)

    # Prepare multipart file upload
    files_payload = [
        ("files", (f.filename, await f.read(), f.content_type))
        for f in files
    ]

    # ───── Step 1: Ingestion Agent ─────
    log_trace("Forwarding files to IngestionAgent", trace_id)
    async with httpx.AsyncClient() as client:
        ingestion_res = await client.post(INGESTION_URL, files=files_payload)

    if ingestion_res.status_code != 200:
        return {"error": "IngestionAgent failed", "trace_id": trace_id}

    parsed_chunks = ingestion_res.json().get("payload", {}).get("chunks", [])
    if not parsed_chunks:
        return {"error": "IngestionAgent returned no chunks", "trace_id": trace_id}

    # ───── Step 2: Retrieval Agent ─────
    log_trace("Forwarding chunks and query to RetrievalAgent", trace_id)
    retrieval_payload = {
        "chunks": parsed_chunks,
        "query": user_query,
        "trace_id": trace_id
    }

    async with httpx.AsyncClient() as client:
        retrieval_res = await client.post(RETRIEVAL_URL, json=retrieval_payload)

    if retrieval_res.status_code != 200:
        return {"error": "RetrievalAgent failed", "trace_id": trace_id}

    top_k_chunks = retrieval_res.json().get("payload", {}).get("retrieved_context", [])
    if not top_k_chunks:
        return {"error": "RetrievalAgent returned no relevant chunks", "trace_id": trace_id}

    # ───── Step 3: LLM Agent ─────
    log_trace("Sending context to LLMResponseAgent", trace_id)
    llm_payload = {
        "query": user_query,
        "top_chunks": top_k_chunks,
        "trace_id": trace_id
    }

    async with httpx.AsyncClient() as client:
        llm_res = await client.post(LLM_URL, json=llm_payload)

    if llm_res.status_code != 200:
        return {"error": "LLMResponseAgent failed", "trace_id": trace_id}

    final_payload = llm_res.json().get("payload", {})
    return {
        "trace_id": trace_id,
        "answer": final_payload.get("answer", "No answer generated"),
        "source_context": final_payload.get("source_context", [])
    }
