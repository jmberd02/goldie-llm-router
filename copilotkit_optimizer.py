"""
Simple Prompt Optimizer using local Ollama

Optimizes prompts for better LLM routing decisions.
"""
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()


class PromptOptimizer:
    """
    Prompt optimizer using local Ollama LLM.
    """
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "qwen3:8b"
        
    def optimize_prompt(
        self, 
        prompt: str, 
        context: Optional[Dict] = None
    ) -> str:
        """
        Optimize a prompt using local Ollama.
        
        Args:
            prompt: Original user prompt
            context: Optional context including thresholds, routing history, etc.
            
        Returns:
            Optimized prompt string
        """
        import requests
        
        # Build the optimization prompt
        system_prompt = self._build_system_prompt(context)
        
        try:
            # Call Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\nOriginal prompt:\n{prompt}\n\nOptimized prompt:",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                optimized = result.get("response", "").strip()
                
                # Clean up any meta-commentary
                optimized = self._clean_response(optimized)
                
                if optimized and len(optimized) > 10 and optimized != prompt:
                    print(f"[Optimizer] Optimized: {len(prompt)} → {len(optimized)} chars")
                    return optimized
                else:
                    return prompt
            else:
                print(f"[Optimizer] Ollama error {response.status_code}")
                return prompt
                
        except Exception as e:
            print(f"[Optimizer] Optimization failed: {e}")
            return prompt
    
    def _build_system_prompt(self, context: Optional[Dict]) -> str:
        """Build system prompt for optimization."""
        system_prompt = """You are an expert Prompt Engineer specializing in LLM routing optimization.

Your task: Rewrite user prompts to be more effective for intelligent routing between small and large language models.

Guidelines:
1. Add clarity and structure to ambiguous requests
2. Break down complex tasks into explicit subtasks when needed
3. Specify expected output format when relevant
4. Add constraints that help with difficulty assessment
5. Preserve the user's original intent completely
6. Keep it concise - don't over-engineer simple requests

CRITICAL: Return ONLY the improved prompt text. No preamble, no explanation, no meta-commentary."""

        if context and context.get("thresholds"):
            thresholds = context["thresholds"]
            system_prompt += "\n\nCurrent routing thresholds:\n"
            for category, value in thresholds.items():
                system_prompt += f"- {category}: {value:.2f}\n"
            system_prompt += "\nConsider these thresholds when optimizing."
        
        return system_prompt
    
    def _clean_response(self, response: str) -> str:
        """Clean up the response to remove meta-commentary."""
        # Remove common prefixes
        prefixes = [
            "Here is the optimized prompt:",
            "Here's the optimized prompt:",
            "Optimized prompt:",
            "The optimized prompt is:",
        ]
        
        for prefix in prefixes:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        # Remove quotes if the entire response is quoted
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        elif response.startswith("'") and response.endswith("'"):
            response = response[1:-1]
        
        return response.strip()

# Singleton instance
_optimizer_instance = None


def get_optimizer() -> PromptOptimizer:
    """Get or create the optimizer singleton."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PromptOptimizer()
    return _optimizer_instance


def optimize_prompt_with_ollama(
    prompt: str, 
    context: Optional[Dict] = None
) -> str:
    """
    Convenience function to optimize a prompt using Ollama.
    
    Args:
        prompt: Original prompt
        context: Optional context dict with thresholds, etc.
        
    Returns:
        Optimized prompt or original if optimization fails
    """
    try:
        optimizer = get_optimizer()
        return optimizer.optimize_prompt(prompt, context)
    except Exception as e:
        print(f"[Optimizer] Optimization failed: {e}")
        return prompt
