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

@router.post("/respond")
async def generate_answer(data: LLMRequest):
    trace_id = data.trace_id

    log_trace("Formatting prompt for LLM with context", trace_id)

    # Construct prompt with context
    context = "\n\n".join(data.top_chunks)
    prompt = f"""
You are an intelligent AI assistant that answers questions based on document context.

Context:
{context}

Question:
{data.query}
""".strip()

    # Generate response using Groq or fallback LLM
    try:
        answer = generate_response(prompt)
        log_trace("LLM generated response successfully", trace_id)
    except Exception as e:
        answer = f"LLM failed: {str(e)}"
        log_trace("LLM generation failed", trace_id)

    # Return answer + source chunks in MCP message
    return build_mcp_message(
        sender="LLMResponseAgent",
        receiver="CoordinatorAgent",
        msg_type="FINAL_ANSWER",
        payload={
            "answer": answer,
            "source_context": data.top_chunks
        },
        trace_id=trace_id
    )
