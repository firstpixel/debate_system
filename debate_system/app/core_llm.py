# app/core_llm.py


import logging
from ollama import Client
from typing import List, Dict, Generator



class LLMClient:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.7, num_predict: int = 512):
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        
        try:
            self.client = Client()
            # Test connection
            self.client.list()
        except Exception as e:
            logging.error(f"Failed to initialize Ollama client: {e}")
            raise ConnectionError(f"Cannot connect to Ollama service. Please ensure Ollama is running. Error: {e}")

    def chat(self, messages: List[Dict]) -> str:
        """Send a chat request to the LLM.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Response content as string
            
        Raises:
            ConnectionError: If Ollama service is unavailable
            ValueError: If model is not found
            RuntimeError: If chat fails
        """
        logging.debug(f"Initiating chat with model {self.model}")
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=False,
                options={
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "frequency_penalty": 0.2,
                    "presence_penalty": 0.3,
                    "num_predict": self.num_predict,
                    "num_ctx": 16384,
                    "mmap": True,
                }
            )
            return response["message"]["content"]
            
        except Exception as e:
            error_msg = str(e).lower()
            if "model" in error_msg and "not found" in error_msg:
                raise ValueError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
            elif "connection" in error_msg or "refused" in error_msg:
                raise ConnectionError(f"Cannot connect to Ollama service: {e}")
            else:
                raise RuntimeError(f"Chat request failed: {e}")

    def stream_chat(self, messages: List[Dict]) -> Generator[str, None, None]:
        """Send a streaming chat request to the LLM.
        
        Args:
            messages: List of message dictionaries
            
        Yields:
            Response chunks as strings
            
        Raises:
            ConnectionError: If Ollama service is unavailable  
            ValueError: If model is not found
            RuntimeError: If streaming fails
        """
        logging.debug(f"Starting stream chat with model: {self.model}")
        
        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.2,
                    "num_predict": self.num_predict,
                    "num_ctx": 16384,
                    "mmap": True,
                }
            )

            for chunk in stream:
                if chunk.get("message", {}).get("content"):
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "model" in error_msg and "not found" in error_msg:
                raise ValueError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
            elif "connection" in error_msg or "refused" in error_msg:
                raise ConnectionError(f"Cannot connect to Ollama service: {e}")
            else:
                raise RuntimeError(f"Streaming chat failed: {e}")

    def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        logging.debug(f"Generating embeddings for text: {text[:50]}...")
        try:
            result = self.client.embeddings(
                model="nomic-embed-text:latest",
                prompt=text,
            )
            return result["embedding"]
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")