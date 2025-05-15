import sys
import os
import site

# Print debug information
def pytest_configure(config):
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    print(f"Site packages: {site.getsitepackages()}")
    
    try:
        import ollama
        print(f"Ollama found at: {ollama.__file__}")
    except ImportError:
        print("Ollama not found in the current Python environment")