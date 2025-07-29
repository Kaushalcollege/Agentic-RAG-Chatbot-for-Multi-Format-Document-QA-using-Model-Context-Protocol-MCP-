from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from utils.vectorstore import vector_db
from utils.mcp import build_mcp_message
from utils.logger import log_trace

router = APIRouter()

class RetrievalRequest(BaseModel):
    chunks: List[str]
    query: str
    trace_id: str

@router.post("/retrieve")
async def retrieve_context(data: RetrievalRequest):
    trace_id = data.trace_id

    # Store new chunks
    vector_db.add_chunks(data.chunks)
    log_trace(f"Stored {len(data.chunks)} chunks in vector DB", trace_id)

    # Query relevant context
    results = vector_db.query(data.query, k=3)
    log_trace(f"Retrieved {len(results)} relevant chunks", trace_id)

    return build_mcp_message(
        sender="RetrievalAgent",
        receiver="CoordinatorAgent",
        msg_type="RETRIEVAL_RESULT",
        payload={
            "retrieved_context": results,
            "query": data.query
        },
        trace_id=trace_id
    )
