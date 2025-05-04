# tests/test_ollama_connection.py

import ollama

def test_ollama_gemma3_responds():
    response = ollama.chat(
        model="gemma3:latest",
        messages=[
            {"role": "system", "content": "You are a helpful debate assistant."},
            {"role": "user", "content": "What are the benefits of AI in education?"}
        ],
        stream=False,
        options={
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 512
        }
    )
    assert response is not None
    assert "message" in response
    print("\nGemma3 Response:", response["message"]["content"])
