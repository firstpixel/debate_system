# memory/qdrant_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance
from uuid import uuid4
from typing import List
from memory.embeddings import embed_text
import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "debate_memory"

class LTMStore:
    def __init__(self, collection_name="debate_memory", vector_size=768):
        self.collection = collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection = COLLECTION_NAME

        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        if self.collection not in collection_names:
            print(f"[Qdrant] Creating missing collection: {self.collection}")
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )


    def store_memory(self, agent_id: str, text: str, tags: List[str]):
        embedding = embed_text(text)
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "agent_id": agent_id,
                "text": text,
                "tags": tags
            }
        )
        self.client.upsert(collection_name=self.collection, points=[point])

    def get_relevant(self, agent_id: str, top_k: int = 5) -> str:
        query_vector = embed_text(agent_id + " memory")
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=Filter(
                must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
            )
        )
        return "\n".join([hit.payload["text"] for hit in results])
    
    def query_ltm(self, agent_id: str, limit: int = 5) -> str:
        results = self.client.scroll(
            collection_name=self.collection,
            scroll_filter={"must": [{"key": "agent_id", "match": {"value": agent_id}}]},
            limit=limit
        )
        return "\n".join(r.payload.get("text", "") for r in results[0])

class RAGRetriever:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection = COLLECTION_NAME

    def query_text(self, query: str, top_k: int = 5) -> str:
        vector = embed_text(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k
        )
        return "\n".join([r.payload["text"] for r in results])
    
    def query_rag(self, agent_id: str, limit: int = 5) -> str:
        results = self.client.scroll(
            collection_name=self.collection,
            scroll_filter={"must": [{"key": "agent_id", "match": {"value": agent_id}}]},
            limit=limit
        )
        return "\n".join(r.payload.get("text", "") for r in results[0])
