# backend/utils/vectorstore.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunk_map = []

    def embed(self, texts):
        return model.encode(texts, convert_to_numpy=True)

    def add_chunks(self, chunks: list[str]):
        vectors = self.embed(chunks)
        if self.index is None:
            self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)
        self.chunk_map.extend(chunks)

    def query(self, question: str, k: int = 3):
        q_vec = self.embed([question])
        distances, indices = self.index.search(q_vec, k)
        return [self.chunk_map[i] for i in indices[0] if i < len(self.chunk_map)]

# Global instance
vector_db = VectorStore()
