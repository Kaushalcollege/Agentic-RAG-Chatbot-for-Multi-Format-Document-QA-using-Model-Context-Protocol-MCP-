from fastapi import APIRouter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

from utils.mcp import build_mcp_message
from utils.parser import parse_file
from utils.logger import log_trace

router = APIRouter()

def intelligent_chunking(full_text: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "],
    )
    return text_splitter.split_text(full_text)

def perform_ingestion(filename: str, file_content: bytes, trace_id: str):
    """Main logic for the ingestion agent, now importable and returns an MCP message."""
    log_trace(f"IngestionAgent: [DEBUG] Parsing document: {filename}", trace_id)
    
    parsed_text = parse_file(filename, file_content)
    chunks = intelligent_chunking(parsed_text)
    
    log_trace(f"IngestionAgent: [DEBUG] Created {len(chunks)} chunks", trace_id)
    
    # Adheres to MCP by wrapping its output
    return build_mcp_message(
        sender="IngestionAgent",
        receiver="CoordinatorAgent",
        msg_type="PARSED_CHUNKS",
        payload={"chunks": chunks},
        trace_id=trace_id
    )