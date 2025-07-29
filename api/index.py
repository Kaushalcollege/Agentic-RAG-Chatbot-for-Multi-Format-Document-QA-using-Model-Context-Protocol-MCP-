from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents import coordinator, ingestion, retrieval, llm_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Using your required agent-based routes
app.include_router(coordinator.router, prefix="/agent/coordinator", tags=["Coordinator"])
app.include_router(ingestion.router, prefix="/agent/ingestion", tags=["Ingestion"])
app.include_router(retrieval.router, prefix="/agent/retrieval", tags=["Retrieval"])
app.include_router(llm_response.router, prefix="/agent/llm", tags=["LLM"])

@app.get("/")
def read_root():
    return {"message": "Agentic RAG Chatbot - MCP Architecture"}