# app/core_llm.py


import logging
from ollama import Client
from typing import List, Dict, Generator



class LLMClient:
    def __init__(self, model: str = "gemma3:latest", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.client = Client()

    def chat(self, messages: List[Dict]) -> str:
        print(f"###########Chatting with model {messages}...") # Use the logger instance
       
        response = self.client.chat(
            model=self.model,
            messages=messages,
            stream=False,
            options={
                "temperature": self.temperature,
                "top_p": 0.7,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.2,
                "num_predict": 512,
                # "num_gpu": 1,  # Ensure we use GPU
                # "num_ctx": 4096,
                "mmap": True,  # Enable memory mapping for better performance
            }
        )
        return response["message"]["content"]

    def stream_chat(self, messages: List[Dict]) -> Generator[str, None, None]:
        print(f"###########Streaming chat with model: {messages}") # Use the logger instance
        stream = self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.2,
                "num_predict": 512,
                # "num_gpu": 1,  # Ensure we use GPU
                # "num_ctx": 4096,
                "mmap": True,  # Enable memory mapping for better performance
            }
        )
        for part in stream:
            yield part["message"]["content"]

    def embed(self, text: str) -> List[float]:
            print(f"###########Embedding with model: {text}") 
            result = self.client.embeddings(
                model="nomic-embed-text:latest",
                prompt=text,
                # options={
                #     "num_gpu": 1  # Ensure embeddings also use GPU
                # }
            )
            return result["embedding"]