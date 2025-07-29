import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunk_map = []
        print("[VectorStore] Initialized.")

    def embed(self, texts):
        print(f"[Embedding] Texts to embed: {len(texts)}")
        vectors = model.encode(texts, convert_to_numpy=True)
        print(f"[Embedding] Shape of vectors: {vectors.shape}")
        return vectors

    def add_chunks(self, chunks: list[str]):
        print(f"[➕ Add Chunks] Adding {len(chunks)} chunks to vector DB.")
        vectors = self.embed(chunks)
        if self.index is None:
            self.index = faiss.IndexFlatL2(vectors.shape[1])
            print("[Index] Created new FAISS index.")
        self.index.add(vectors)
        print(f"[Index] Total vectors in index: {self.index.ntotal}")
        self.chunk_map.extend(chunks)
        print(f"[Chunk Map] Total chunks tracked: {len(self.chunk_map)}")

    def query(self, question: str, k: int = 3):
        print(f"[❓ Query] Received question: '{question}'")
        q_vec = self.embed([question])
        distances, indices = self.index.search(q_vec, k)
        print(f"[FAISS Search] Distances: {distances}")
        print(f"[Indices] Retrieved indices: {indices}")
        results = [self.chunk_map[i] for i in indices[0] if i < len(self.chunk_map)]
        print(f"[Result] Top {k} chunks: {results}")
        return results

# Global instance
vector_db = VectorStore()
