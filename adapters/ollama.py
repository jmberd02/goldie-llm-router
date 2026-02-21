"""Ollama adapter for local model inference."""

import time
import requests
from models import CompletionResult


class OllamaAdapter:
    """Adapter for Ollama local models."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_map = {
            "small": "llama3.2:3b",  # Standard llama3.2 3B model
        }
    
    def complete(self, prompt: str, model_id: str) -> CompletionResult:
        """
        Send a completion request to Ollama.
        
        Args:
            prompt: The prompt to send
            model_id: "small" (maps to qwen3:8b)
        
        Returns:
            CompletionResult with response and metrics
        """
        start_time = time.time()
        
        # Map model_id to actual Ollama model name
        ollama_model = self.model_map.get(model_id, "qwen3:8b")
        
        # Make request to Ollama
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=180,  # Increased to 3 minutes for slow responses
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract response and metrics
        text = data.get("response", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return CompletionResult(
            response=text,
            model_used="small",
            model_id=ollama_model,
            routing_reason="",
            escalated=False,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=0.0,  # Ollama is free
            latency_ms=latency_ms,
            classification=None,
        )
