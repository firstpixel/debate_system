import logging
import numpy as np
from typing import Dict, List, Optional
from sklearn.metrics.pairwise import cosine_similarity
from ollama import Client
import os

from app.memory_manager import MemoryManager
from app.core_llm import LLMClient
from app.contradiction_detector import ContradictionDetector
from app.contradiction_log import ContradictionLog

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)


class BayesianTracker:
    def __init__(
        self,
        embedding_model: str = "nomic-embed-text:latest",
        contradiction_threshold: float = 0.4,
        llm: Optional[LLMClient] = None,
        memory: Optional[MemoryManager] = None
    ):
        self.embedding_model = embedding_model
        self.client = Client()
        self.agent_history: Dict[str, List[str]] = {}
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.topic_embedding: Optional[np.ndarray] = None

        self.memory = memory or MemoryManager()
        self.llm = llm or LLMClient()
        self.detector = ContradictionDetector(model_name=embedding_model, use_llm_fallback=True)
        self.contradiction_log = ContradictionLog()

        self.coherence_scores: Dict[str, float] = {}
        self.contradiction_threshold = contradiction_threshold

    def _get_embedding(self, text: str) -> np.ndarray:
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        logger.info(f"Embedding text with model {self.embedding_model}...")
        vec = np.array(self.client.embeddings(model=self.embedding_model, prompt=text)["embedding"])
        self.embeddings_cache[text] = vec
        return vec

    def reset(self):
        self.agent_history.clear()
        self.embeddings_cache.clear()
        self.contradiction_log.entries.clear()
        self.coherence_scores.clear()
        self.topic_embedding = None

    def track_turn(self, agent: str, message: str, topic: str):
        logger.info(f"Tracking new turn for {agent}")
        self.agent_history.setdefault(agent, []).append(message)

        # Embed topic once
        if self.topic_embedding is None:
            self.topic_embedding = self._get_embedding(topic)

        analysis = self._analyze_semantics(agent)
        contradiction_data = self._detect_contradiction(agent, message)

        if contradiction_data["contradicted"]:
            self.contradiction_log.log(
                agent=agent,
                new_belief=message,
                contradicted=contradiction_data["contradicted"],
                similarity_scores=contradiction_data["scores"]
            )

        turn_id = self.memory.add_turn(agent, message)
        self.memory.save_belief(agent, {
            "latest_statement": message,
            "drift": analysis["drift"],
            "coherence": analysis["coherence"],
            "contradiction": contradiction_data["flag"],
            "turn_id": turn_id
        })

        self.coherence_scores[agent] = analysis["coherence"]

        return {
            **analysis,
            "contradicted_beliefs": contradiction_data["contradicted"]
        }

    def _analyze_semantics(self, agent: str) -> Dict:
        if agent not in self.agent_history or len(self.agent_history[agent]) < 2:
            return {"coherence": 1.0, "drift": 0.0}

        last = self.agent_history[agent][-2]
        current = self.agent_history[agent][-1]

        vec_last = self._get_embedding(last)
        vec_current = self._get_embedding(current)

        coherence = float(cosine_similarity([vec_last], [vec_current])[0][0])
        drift = 1.0 - float(cosine_similarity([vec_current], [self.topic_embedding])[0][0])

        return {
            "coherence": round(coherence, 3),
            "drift": round(drift, 3)
        }

    def _detect_contradiction(self, agent: str, new_claim: str) -> Dict:
        belief_str = self.memory.get_context(agent_id=agent, strategy="belief")
        beliefs = belief_str.splitlines() if isinstance(belief_str, str) else []
        beliefs = [b.lstrip("- ").strip() for b in beliefs if b.strip()]

        if not beliefs:
            return {"flag": False, "contradicted": [], "scores": []}

        new_emb = self._get_embedding(new_claim)
        # Defensive: skip if embedding is empty or invalid
        if not isinstance(new_emb, (list, np.ndarray)) or len(new_emb) == 0:
            return {"flag": False, "contradicted": [], "scores": []}

        contradictions = []
        scores = []

        for belief in beliefs:
            belief_emb = self._get_embedding(belief)
            # Defensive: skip if embedding is empty or mismatched
            if not isinstance(belief_emb, (list, np.ndarray)) or len(belief_emb) == 0 or len(belief_emb) != len(new_emb):
                continue
            similarity = float(cosine_similarity([new_emb], [belief_emb])[0][0])
            scores.append((belief, similarity))
            if similarity >= self.contradiction_threshold:
                contradictions.append(belief)

        verified = self.detector.verify_with_llm(new_claim, contradictions) if contradictions else ""

        return {
            "flag": bool(contradictions),
            "contradicted": contradictions,
            "verified_explanation": verified,
            "scores": scores
        }

    def get_scores(self) -> Dict[str, float]:
        result = {}
        for agent in self.agent_history:
            score_block = self.get_agent_scores(agent)
            if isinstance(score_block, dict):
                result[agent] = score_block.get("coherence", 1.0)
            else:
                logger.warning(f"Unexpected score format for agent {agent}: {score_block}")
                result[agent] = 1.0
        return result

    def get_agent_scores(self, agent: str) -> Dict:
        try:
            scores = self.memory.belief.get_belief_summary(agent)
            return scores if isinstance(scores, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get belief summary for {agent}: {e}")
            return {}

    def export_logs(self) -> str:
        return self.contradiction_log.to_markdown()

    def update(self, agent: str, message: str):
        return self.track_turn(agent, message, topic="N/A")
