from pydantic import BaseModel
from typing import List, Dict, Optional
from sentence_transformers.cross_encoder import CrossEncoder
from vercel_kv import get
import pickle

from utils.mcp import build_mcp_message
from utils.logger import log_trace
from utils.llm import generate_response

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rewrite_query(user_query: str, chat_history: list, trace_id: str) -> str:
    if not chat_history:
        log_trace("RetrievalAgent: [DEBUG] No chat history, using original query.", trace_id)
        return user_query
    
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"Given the chat history and a follow up question, rephrase it to be a standalone question.\n\nHistory:\n{history_str}\n\nFollow Up: {user_query}\nStandalone Question:"
    log_trace("RetrievalAgent: [DEBUG] Rewriting query with history.", trace_id)
    return generate_response(prompt)

def perform_retrieval(session_id: str, user_query: str, chat_history: list, trace_id: str):
    """Main logic for the retrieval agent, now importable and returns an MCP message."""
    log_trace("RetrievalAgent: [DEBUG] Starting retrieval process.", trace_id)
    
    try:
        db_bytes = get(session_id)
        if not db_bytes: 
            log_trace(f"RetrievalAgent ERROR: Session not found in KV store.", trace_id)
            return build_mcp_message("RetrievalAgent", "CoordinatorAgent", "ERROR", {"error": "Invalid session_id"}, trace_id)
        db = pickle.loads(db_bytes)
    except Exception as e:
        log_trace(f"RetrievalAgent ERROR: {e}", trace_id)
        return build_mcp_message("RetrievalAgent", "CoordinatorAgent", "ERROR", {"error": f"KV Error: {e}"}, trace_id)

    standalone_query = rewrite_query(user_query, chat_history, trace_id)
    log_trace(f"RetrievalAgent: [DEBUG] Standalone query is '{standalone_query}'", trace_id)

    initial_chunks = db.query(standalone_query, k=10)
    
    sentence_pairs = [[standalone_query, chunk] for chunk in initial_chunks]
    scores = cross_encoder.predict(sentence_pairs)
    scored_chunks = sorted(zip(scores, initial_chunks), reverse=True)
    reranked_chunks = [chunk for score, chunk in scored_chunks[:3]]
    
    log_trace(f"RetrievalAgent: [DEBUG] Found {len(reranked_chunks)} re-ranked chunks", trace_id)
    
    # Adheres to MCP by wrapping its output
    return build_mcp_message(
        sender="RetrievalAgent",
        receiver="CoordinatorAgent",
        msg_type="RETRIEVAL_RESULT",
        payload={"retrieved_context": reranked_chunks},
        trace_id=trace_id
    )