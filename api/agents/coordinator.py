import uuid
import asyncio
import functools
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional
from vercel_kv import set, expire
import pickle

from utils.mcp import build_mcp_message
from utils.logger import log_trace
from utils.vectorstore import VectorStore
from utils.llm import generate_response
from agents.ingestion import perform_ingestion
from agents.retrieval import perform_retrieval
from agents.llm_response import perform_llm_response

router = APIRouter()

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

Extracted Sentence:"""
    return generate_response(prompt)

@router.post("/start_session")
async def start_session_handler(file: UploadFile = File(...)):
    session_id = f"session-{str(uuid.uuid4())[:8]}"
    trace_id = f"trace-{session_id}"
    log_trace(f"Coordinator: [DEBUG] Starting new session {session_id}", trace_id)

    file_content = await file.read()
    ingestion_result = perform_ingestion(file.filename, file_content, trace_id)
    
    # Unpack the MCP message from the Ingestion agent
    parsed_chunks = ingestion_result.get("payload", {}).get("chunks", [])
    if not parsed_chunks:
        log_trace("Coordinator: ERROR - Ingestion agent returned no chunks", trace_id)
        # Handle error appropriately
        return {"error": "Failed to parse document."}

    db = VectorStore()
    db.add_chunks(parsed_chunks)
    
    set(session_id, pickle.dumps(db))
    expire(session_id, 3600)
    log_trace(f"Coordinator: [DEBUG] Vector store created and saved for {session_id}", trace_id)

    return build_mcp_message(
        "CoordinatorAgent", "Frontend", "SESSION_STARTED",
        {"session_id": session_id, "chunks_processed": len(parsed_chunks)},
        trace_id
    )

@router.post("/query")
async def query_handler(request: QueryRequest):
    session_id = request.session_id
    trace_id = f"trace-{session_id}"
    log_trace(f"Coordinator: [DEBUG] Received query for session {session_id}", trace_id)

    retrieval_result = perform_retrieval(session_id, request.user_query, request.chat_history or [], trace_id)
    
    # Unpack the MCP message from the Retrieval agent
    retrieved_chunks = retrieval_result.get("payload", {}).get("retrieved_context", [])
    if not retrieved_chunks:
        log_trace("Coordinator: ERROR - Retrieval agent returned no chunks", trace_id)
        return {"error": "Could not retrieve relevant context"}

    llm_result = perform_llm_response(request.user_query, retrieved_chunks, trace_id)

    # Unpack the MCP message from the LLM agent
    final_payload = llm_result.get("payload", {})
    final_answer = final_payload.get("answer", "No answer generated")
    
    log_trace("Coordinator: [DEBUG] Extracting final precise snippets", trace_id)
    tasks_to_run = [functools.partial(extract_precise_snippet, final_answer, p) for p in retrieved_chunks]
    precise_snippets = await asyncio.gather(*[asyncio.to_thread(func) for func in tasks_to_run])

    log_trace("Coordinator: [DEBUG] Returning final answer to frontend", trace_id)
    return {"answer": final_answer, "source_context": precise_snippets}