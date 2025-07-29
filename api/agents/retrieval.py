from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
from sentence_transformers.cross_encoder import CrossEncoder
from vercel_kv import get
import pickle

from utils.mcp import build_mcp_message
from utils.logger import log_trace
from utils.llm import generate_response

router = APIRouter()
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

class RetrievalRequest(BaseModel):
    session_id: str
    user_query: str
    chat_history: Optional[List[Dict[str, str]]] = None

def rewrite_query(user_query: str, chat_history: list) -> str:
    if not chat_history:
        return user_query
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"Given the chat history and a follow up question, rephrase it to be a standalone question.\n\nHistory:\n{history_str}\n\nFollow Up: {user_query}\nStandalone Question:"
    return generate_response(prompt)

def perform_retrieval(session_id: str, user_query: str, chat_history: list) -> List[str]:
    """Main logic for the retrieval agent, now importable."""
    trace_id = f"trace-{session_id}"
    log_trace("RetrievalAgent: Received query", trace_id)
    
    try:
        db_bytes = get(session_id)
        if not db_bytes: 
            log_trace(f"RetrievalAgent ERROR: Session not found in KV store.", trace_id)
            return []
        db = pickle.loads(db_bytes)
    except Exception as e:
        log_trace(f"RetrievalAgent ERROR: {e}", trace_id)
        return []

    standalone_query = rewrite_query(user_query, chat_history)
    log_trace(f"RetrievalAgent: Standalone query is '{standalone_query}'", trace_id)

    initial_chunks = db.query(standalone_query, k=10)
    
    sentence_pairs = [[standalone_query, chunk] for chunk in initial_chunks]
    scores = cross_encoder.predict(sentence_pairs)
    scored_chunks = sorted(zip(scores, initial_chunks), reverse=True)
    reranked_chunks = [chunk for score, chunk in scored_chunks[:3]]
    log_trace(f"RetrievalAgent: Found {len(reranked_chunks)} re-ranked chunks", trace_id)
    return reranked_chunks

@router.post("/retrieve")
async def retrieve_context_endpoint(request: RetrievalRequest):
    """This endpoint is kept for architectural compliance but is not used in the main Vercel flow."""
    chunks = perform_retrieval(request.session_id, request.user_query, request.chat_history or [])
    return build_mcp_message("RetrievalAgent", "CoordinatorAgent", "RETRIEVAL_RESULT", {"retrieved_context": chunks})