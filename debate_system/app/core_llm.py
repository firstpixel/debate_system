# app/core_llm.py


import logging
from ollama import Client
from typing import List, Dict, Generator

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.client = Client()

    def chat(self, messages: List[Dict]) -> str:
        logger.info(f"###########Chatting with model {self.model}...") # Use the logger instance
       
        response = self.client.chat(
            model=self.model,
            messages=messages,
            stream=False,
            options={
                "temperature": self.temperature,
                "top_p": 0.7,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "num_predict": 256,
                "num_gpu": 1, 
                "num_ctx": 64000,
            }
        )
        return response["message"]["content"]

    def stream_chat(self, messages: List[Dict]) -> Generator[str, None, None]:
        logger.info(f"###########Streaming chat with model: {self.model}") # Use the logger instance
        stream = self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "num_predict": 512
            }
        )
        for part in stream:
            yield part["message"]["content"]

    def embed(self, text: str) -> List[float]:
            logger.info("###########Embedding with model: nomic-embed-text:latest")
            result = self.client.embeddings(
                model="nomic-embed-text:latest",
                prompt=text
            )
            return result["embedding"]