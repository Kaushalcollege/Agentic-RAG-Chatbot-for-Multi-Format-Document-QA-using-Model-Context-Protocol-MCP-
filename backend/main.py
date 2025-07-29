from fastapi import FastAPI
from agents import coordinator, ingestion, retrieval, llm_response

app = FastAPI()

# Routes from each agent
app.include_router(coordinator.router, prefix="/agent/coordinator")
app.include_router(ingestion.router, prefix="/agent/ingestion")
app.include_router(retrieval.router, prefix="/agent/retrieval")
app.include_router(llm_response.router, prefix="/agent/llm")

@app.get("/")
def read_root():
    return {"message": "Agentic RAG Chatbot"}
