import uuid
import httpx
import asyncio
import functools
from fastapi import APIRouter
from pydantic import BaseModel # <-- This line is now corrected
from typing import List, Dict, Optional
from sentence_transformers.cross_encoder import CrossEncoder

from agents.upload import vector_stores
from utils.logger import log_trace
from utils.llm import generate_response

router = APIRouter()
LLM_URL = "http://localhost:8000/agent/llm/respond"
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
log_trace("Cross-Encoder model loaded.", "SYSTEM")

class QueryRequest(BaseModel):
    session_id: str
    user_query: str
    chat_history: Optional[List[Dict[str, str]]] = None

def rewrite_query(user_query: str, chat_history: list) -> str:
    if not chat_history:
        return user_query
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"Given the chat history and a follow up question, rephrase it to be a standalone question.\n\nHistory:\n{history_str}\n\nFollow Up: {user_query}\nStandalone Question:"
    return generate_response(prompt)

def extract_precise_snippet(answer: str, source_paragraph: str) -> str:
    prompt = f"""From the 'Source Text' below, extract the single sentence that is most relevant to the given 'Answer'. Return only that sentence.

Answer:
"{answer}"

Source Text:
"{source_paragraph}"

Most Relevant Sentence:"""
    return generate_response(prompt)

@router.post("/ask")
async def query_handler(request: QueryRequest):
    trace_id = f"trace-{str(uuid.uuid4())[:8]}"
    session_id = request.session_id
    user_query = request.user_query
    chat_history = request.chat_history or []
    
    log_trace(f"Received query for session_id: {session_id}", trace_id)

    standalone_query = rewrite_query(user_query, chat_history)
    log_trace(f"Original: '{user_query}' | Standalone: '{standalone_query}'", trace_id)

    db = vector_stores.get(session_id)
    if not db:
        return {"error": "Invalid session_id", "trace_id": trace_id}
    
    initial_chunks = db.query(standalone_query, k=10)
    if not initial_chunks:
        return {"error": "Could not retrieve context.", "trace_id": trace_id}

    sentence_pairs = [[standalone_query, chunk] for chunk in initial_chunks]
    scores = cross_encoder.predict(sentence_pairs)
    scored_chunks = sorted(zip(scores, initial_chunks), reverse=True)
    top_paragraphs = [chunk for score, chunk in scored_chunks[:3]]

    llm_payload = { "query": user_query, "top_chunks": top_paragraphs, "trace_id": trace_id }
    async with httpx.AsyncClient() as client:
        llm_res = await client.post(LLM_URL, json=llm_payload)

    if llm_res.status_code != 200:
        return {"error": "LLMResponseAgent failed", "trace_id": trace_id}

    final_payload = llm_res.json().get("payload", {})
    final_answer = final_payload.get("answer", "No answer generated")
    
    tasks_to_run = [
        functools.partial(extract_precise_snippet, final_answer, p)
        for p in top_paragraphs
    ]
    precise_snippets = await asyncio.gather(*[asyncio.to_thread(func) for func in tasks_to_run])

    return {
        "trace_id": trace_id,
        "answer": final_answer,
        "source_context": precise_snippets
    }