import logging
import numpy as np
from typing import List
import ollama
from app.core_llm import LLMClient

logger = logging.getLogger(__name__)

class ContradictionDetector:
    def __init__(self, model_name="nomic-embed-text:latest", use_llm_fallback=True):
        self.model_name = model_name
        self.llm = LLMClient(model="gemma3:latest", temperature=0.2)
        self.use_llm = use_llm_fallback

    def _embed(self, text: str) -> List[float]:
        logger.info(f"###########Embedding text with model {self.model_name}...")
        return ollama.embeddings(model=self.model_name, prompt=text)["embedding"]

    def _cosine_similarity(self, a, b):
        if a is None or b is None or len(a) == 0 or len(b) == 0:
            return 0.0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def find_contradictions(self, new_statement: str, belief_memory: List[str], threshold: float = 0.4) -> List[str]:
        if not belief_memory:
            return []

        new_emb = np.array(self._embed(new_statement))
        if new_emb is None or len(new_emb) == 0:
            return []  # Safety check

        contradictions = []

        for belief in belief_memory:
            belief_emb = np.array(self._embed(belief))
            if belief_emb is None or len(belief_emb) == 0:
                continue  # Skip invalid embeddings

            similarity = self._cosine_similarity(new_emb, belief_emb)
            if similarity < threshold:
                contradictions.append(belief)

        return contradictions


    def verify_with_llm(self, new_statement: str, beliefs: List[str]) -> str:
        if not self.use_llm or not beliefs:
            return ""

        bullets = "\n".join(f"- {b}" for b in beliefs)
        prompt = [
            {"role": "system", "content": "You are a contradiction checker. Identify if the new claim contradicts the beliefs."},
            {"role": "user", "content": f"### Beliefs:\n{bullets}\n\n### New Claim:\n{new_statement}\n\nIs there a contradiction? Respond in Markdown."}
        ]

        # Replace streaming with non-streaming call since result isn't shown in UI
        return self.llm.chat(prompt)
