from fastapi import APIRouter, UploadFile, File
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

from utils.mcp import build_mcp_message
from utils.parser import parse_file
from utils.logger import log_trace

router = APIRouter()

def intelligent_chunking(full_text: str) -> list[str]:
    """Splits text into small, focused chunks for better retrieval."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "],
    )
    return text_splitter.split_text(full_text)

@router.post("/parse")
async def parse_documents(files: List[UploadFile] = File(...)):
    trace_id = f"trace-{files[0].filename}"
    log_trace(f"IngestionAgent: Parsing {len(files)} document(s)", trace_id)

    all_chunks = []
    for file in files:
        content = await file.read()
        parsed_text = parse_file(file.filename, content)
        chunks = intelligent_chunking(parsed_text)
        all_chunks.extend(chunks)

    log_trace(f"IngestionAgent: Created {len(all_chunks)} chunks", trace_id)

    return build_mcp_message(
        sender="IngestionAgent",
        receiver="CoordinatorAgent",
        msg_type="PARSED_CHUNKS",
        payload={"chunks": all_chunks},
        trace_id=trace_id
    )