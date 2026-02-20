"""Hybrid adapter that routes between Ollama (small) and Bedrock (large)."""

from models import CompletionResult
from adapters.ollama import OllamaAdapter
from adapters.bedrock import BedrockAdapter


class HybridAdapter:
    """
    Hybrid adapter that uses:
    - Ollama (qwen2.5:1.5b) for small model requests
    - Bedrock (Claude Sonnet) for large model requests
    """
    
    def __init__(self):
        self.ollama = OllamaAdapter()
        self.bedrock = BedrockAdapter()
    
    def complete(self, prompt: str, model_id: str) -> CompletionResult:
        """
        Route to appropriate adapter based on model_id.
        
        Args:
            prompt: The prompt to send
            model_id: "haiku" or "small" → Ollama, "sonnet" → Bedrock
        
        Returns:
            CompletionResult from the appropriate adapter
        """
        # Route haiku requests to Ollama (small model)
        if model_id in ("haiku", "small"):
            return self.ollama.complete(prompt, "small")
        
        # Route sonnet requests to Bedrock (large model)
        elif model_id == "sonnet":
            return self.bedrock.complete(prompt, "sonnet")
        
        else:
            raise ValueError(f"Unknown model_id: {model_id}")
