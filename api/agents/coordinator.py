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

# Import agent logic directly
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
    log_trace(f"Coordinator: Starting new session {session_id}", trace_id)

    # Step 1: Call Ingestion Agent's logic directly
    file_content = await file.read()
    parsed_chunks = perform_ingestion(file.filename, file_content)

    # Step 2: Create and store the Vector DB
    db = VectorStore()
    db.add_chunks(parsed_chunks)
    
    set(session_id, pickle.dumps(db))
    expire(session_id, 3600)
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

    # Step 1: Call Retrieval Agent's logic directly
    retrieved_chunks = perform_retrieval(
        session_id, request.user_query, request.chat_history or []
    )
    if not retrieved_chunks:
        return {"error": "Could not retrieve relevant context"}

    # Step 2: Call LLM Agent's logic directly
    final_answer = perform_llm_response(
        request.user_query, retrieved_chunks, trace_id
    )
    
    # Step 3: Extract precise snippets
    tasks_to_run = [
        functools.partial(extract_precise_snippet, final_answer, p) 
        for p in retrieved_chunks
    ]
    precise_snippets = await asyncio.gather(*[asyncio.to_thread(func) for func in tasks_to_run])

    # Step 4: Return final, clean JSON to the frontend
    return {"answer": final_answer, "source_context": precise_snippets}