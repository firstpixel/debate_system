# memory/embeddings.py

from typing import List
from app.core_llm import LLMClient

llm = LLMClient()

def embed_text(text: str) -> List[float]:
    try:
        embedding = llm.embed(text)
        if isinstance(embedding, list) and len(embedding) > 0:
            return embedding
        else:
            return [0.0] * 768  # Fallback: zero vector with expected dimension
    except Exception as e:
        print(f"[embed_text] Error embedding text: {e}")
        return [0.0] * 768  # Fail-safe embedding

