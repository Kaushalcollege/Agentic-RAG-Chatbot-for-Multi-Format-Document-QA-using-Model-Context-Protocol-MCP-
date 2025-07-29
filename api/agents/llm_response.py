from typing import List
from utils.llm import generate_response
from utils.mcp import build_mcp_message
from utils.logger import log_trace

def perform_llm_response(query: str, top_chunks: List[str], trace_id: str):
    """Main logic for the LLM agent, now importable and returns an MCP message."""
    log_trace("LLMResponseAgent: [DEBUG] Received context for final answer generation.", trace_id)
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
        log_trace("LLMResponseAgent: [DEBUG] Generated answer.", trace_id)
        # Adheres to MCP by wrapping its output
        return build_mcp_message(
            sender="LLMResponseAgent",
            receiver="CoordinatorAgent",
            msg_type="FINAL_ANSWER",
            payload={"answer": answer, "source_context": top_chunks},
            trace_id=trace_id
        )
    except Exception as e:
        log_trace(f"LLM generation failed: {e}", trace_id)
        return build_mcp_message("LLMResponseAgent", "CoordinatorAgent", "ERROR", {"error": f"LLM failed: {e}"}, trace_id)