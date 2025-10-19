import uuid
import httpx
import asyncio
import functools
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional

from utils.mcp import build_mcp_message
from utils.logger import log_trace
from utils.vectorstore import VectorStore
from utils.llm import generate_response
from agents.retrieval import session_vector_stores

router = APIRouter()

INGESTION_URL = "/agent/ingestion/parse"
RETRIEVAL_URL = "/agent/retrieval/retrieve"
LLM_URL = "/agent/llm/respond"

class QueryRequest(BaseModel):
    session_id: str
    user_query: str
    chat_history: Optional[List[Dict[str, str]]] = None

def extract_precise_snippet(answer: str, source_paragraph: str) -> str:
    prompt = f"""[BEGIN DATA]
==
Answer: "{answer}"
==
Source Text: "{source_paragraph}"
==
[END DATA]

Instructions: From the "Source Text" above, find and return the chunk that best supports the "Answer". Try to Impress the user with your knowledge.

Sentence:"""
    return generate_response(prompt)

@router.post("/start_session")
async def start_session_handler(file: UploadFile = File(...)):
    session_id = f"session-{str(uuid.uuid4())[:8]}"
    trace_id = f"trace-{session_id}"
    log_trace(f"Coordinator: Starting new session {session_id}", trace_id)

    files_payload = [("files", (file.filename, await file.read(), file.content_type))]
    async with httpx.AsyncClient(timeout=60.0) as client:
        ingestion_res = await client.post(INGESTION_URL, files=files_payload)
    
    parsed_chunks = ingestion_res.json().get("payload", {}).get("chunks", [])

    db = VectorStore()
    db.add_chunks(parsed_chunks)
    session_vector_stores[session_id] = db
    log_trace(f"Coordinator: Vector store created for {session_id}", trace_id)

    return build_mcp_message(
        sender="CoordinatorAgent",
        receiver="Frontend",
        msg_type="SESSION_STARTED",
        payload={"session_id": session_id, "chunks_processed": len(parsed_chunks)},
        trace_id=trace_id
    )

@router.post("/query")
async def query_handler(request: QueryRequest):
    session_id = request.session_id
    trace_id = f"trace-{session_id}"
    log_trace("Coordinator: Received query", trace_id)

    retrieval_payload = request.dict()
    async with httpx.AsyncClient(timeout=60.0) as client:
        retrieval_res = await client.post(RETRIEVAL_URL, json=retrieval_payload)
    
    retrieved_chunks = retrieval_res.json().get("payload", {}).get("retrieved_context", [])

    llm_payload = {"query": request.user_query, "top_chunks": retrieved_chunks, "trace_id": trace_id}
    async with httpx.AsyncClient(timeout=60.0) as client:
        llm_res = await client.post(LLM_URL, json=llm_payload)

    final_payload = llm_res.json().get("payload", {})
    final_answer = final_payload.get("answer", "No answer generated")

    tasks_to_run = [functools.partial(extract_precise_snippet, final_answer, p) for p in retrieved_chunks]
    precise_snippets = await asyncio.gather(*[asyncio.to_thread(func) for func in tasks_to_run])

    return { "answer": final_answer, "source_context": precise_snippets }