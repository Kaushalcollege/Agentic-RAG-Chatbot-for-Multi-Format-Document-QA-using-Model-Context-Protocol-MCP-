from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from utils.llm import generate_response
from utils.mcp import build_mcp_message
from utils.logger import log_trace

router = APIRouter()

class LLMRequest(BaseModel):
    query: str
    top_chunks: List[str]
    trace_id: str

def perform_llm_response(query: str, top_chunks: List[str], trace_id: str) -> str:
    """Main logic for the LLM agent, now importable."""
    log_trace("LLMResponseAgent: Received context", trace_id)
    context = "\n\n".join(top_chunks)
    prompt = f"""
You are an intelligent AI assistant that answers questions based on document context.

Context:
{context}

Question:
{query}
""".strip()
    try:
        answer = generate_response(prompt)
        log_trace("LLMResponseAgent: Generated answer", trace_id)
        return answer
    except Exception as e:
        log_trace(f"LLM generation failed: {e}", trace_id)
        return f"LLM failed: {str(e)}"

@router.post("/respond")
async def generate_answer_endpoint(data: LLMRequest):
    """This endpoint is kept for architectural compliance but is not used in the main Vercel flow."""
    answer = perform_llm_response(data.query, data.top_chunks, data.trace_id)
    return build_mcp_message(
        "LLMResponseAgent", "CoordinatorAgent", "FINAL_ANSWER", 
        {"answer": answer, "source_context": data.top_chunks}
    )