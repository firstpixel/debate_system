# app/integration_plugin.py

from typing import Dict, Callable, Any
import requests

plugin_registry: Dict[str, Callable] = {}

def register_plugin(name: str):
    def wrapper(cls):
        plugin_registry[name] = cls
        return cls
    return wrapper

def run_plugin(name: str, input_data: Dict[str, Any]) -> Dict:
    if name not in plugin_registry:
        raise ValueError(f"Plugin not registered: {name}")

    plugin = plugin_registry[name]()
    return plugin.run(input_data)

# REST-style plugin (useful for validators, search APIs, etc.)
def run_rest_plugin(url: str, input_data: Dict[str, Any]) -> Dict:
    try:
        response = requests.post(url, json=input_data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Example usage
# data = run_rest_plugin("http://localhost:8000/validate", {"text": "AI is risky."})

# @register_plugin("example_plugin")
# class ExamplePlugin:
#     def run(self, input_data: Dict[str, Any]) -> Dict:
#         # Example processing
#         return {"processed_data": input_data}