from fastapi import APIRouter, UploadFile, File
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

from utils.mcp import build_mcp_message
from utils.parser import parse_file
from utils.logger import log_trace

router = APIRouter()

def intelligent_chunking(full_text: str) -> list[str]:
    """Splits text into small, focused chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "],
    )
    return text_splitter.split_text(full_text)

def perform_ingestion(filename: str, file_content: bytes) -> List[str]:
    """Main logic for the ingestion agent, now importable."""
    trace_id = f"trace-{filename}"
    log_trace(f"IngestionAgent: Parsing document", trace_id)
    
    parsed_text = parse_file(filename, file_content)
    chunks = intelligent_chunking(parsed_text)
    
    log_trace(f"IngestionAgent: Created {len(chunks)} chunks", trace_id)
    return chunks

@router.post("/parse")
async def parse_documents_endpoint(files: List[UploadFile] = File(...)):
    """This endpoint is kept for architectural compliance but is not used in the main Vercel flow."""
    content = await files[0].read()
    chunks = perform_ingestion(files[0].filename, content)
    return build_mcp_message("IngestionAgent", "CoordinatorAgent", "PARSED_CHUNKS", {"chunks": chunks})