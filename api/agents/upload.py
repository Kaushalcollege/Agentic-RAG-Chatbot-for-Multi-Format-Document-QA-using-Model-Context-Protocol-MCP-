import uuid
from fastapi import APIRouter, File, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

from utils.parser import parse_file
from utils.vectorstore import VectorStore
from utils.logger import log_trace

router = APIRouter()
vector_stores = {}

def intelligent_chunking(full_text: str) -> list[str]:
    """Splits a large text into smaller, semantically relevant chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        # THE FIX: Reduce chunk size for more focused context.
        chunk_size=300,  # Reduced from 1000
        chunk_overlap=50,  # Reduced from 200
        length_function=len,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "],
    )
    return text_splitter.split_text(full_text)

@router.post("/process")
async def process_document(file: UploadFile = File(...)):
    trace_id = f"trace-{str(uuid.uuid4())[:8]}"
    log_trace(f"Processing document: {file.filename}", trace_id)

    content = await file.read()
    parsed_text = parse_file(file.filename, content)
    chunks = intelligent_chunking(parsed_text)
    log_trace(f"Created {len(chunks)} chunks from document", trace_id)

    db = VectorStore()
    db.add_chunks(chunks)

    session_id = f"session-{str(uuid.uuid4())[:8]}"
    vector_stores[session_id] = db
    log_trace(f"Vector store created for session_id: {session_id}", trace_id)

    return {
        "session_id": session_id,
        "file_name": file.filename,
        "chunks_processed": len(chunks)
    }