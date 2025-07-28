# backend/agents/ingestion.py
from fastapi import APIRouter, UploadFile, File
from utils.mcp import build_mcp_message
from utils.parser import parse_file
from utils.logger import log_trace

router = APIRouter()

@router.post("/parse")
async def parse_documents(files: list[UploadFile] = File(...)):
    trace_id = f"trace-{files[0].filename}"  # Simplified

    all_chunks = []
    for file in files:
        content = await file.read()
        parsed_text = parse_file(file.filename, content)
        chunks = [chunk.strip() for chunk in parsed_text.split("\n\n") if chunk.strip()]
        all_chunks.extend(chunks)

    log_trace(f"Parsed {len(all_chunks)} chunks from uploaded documents", trace_id)

    return build_mcp_message(
        sender="IngestionAgent",
        receiver="CoordinatorAgent",
        msg_type="PARSED_CHUNKS",
        payload={"chunks": all_chunks},
        trace_id=trace_id
    )
