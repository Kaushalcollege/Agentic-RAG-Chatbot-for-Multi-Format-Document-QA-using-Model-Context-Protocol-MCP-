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
    log_trace("LLMResponseAgent: Received context", trace_id)

    context = "\n\n".join(data.top_chunks)
    prompt = f"""You are a helpful AI assistant that answers user questions based on the provided document context.

- For specific questions, find the answer in the provided context and respond directly.

Context from the document:
---
{context}
---

Question: {data.query}"""

    answer = generate_response(prompt)
    log_trace("LLMResponseAgent: Generated answer", trace_id)

    return build_mcp_message(
        sender="LLMResponseAgent",
        receiver="CoordinatorAgent",
        msg_type="FINAL_ANSWER",
        payload={"answer": answer, "source_context": data.top_chunks},
        trace_id=trace_id
    )