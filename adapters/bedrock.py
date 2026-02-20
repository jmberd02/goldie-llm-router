import boto3
import json
import time
import os
from pathlib import Path
from models import CompletionResult


class BedrockAdapter:
    """Adapter for Amazon Bedrock Claude models using the Converse API."""
    
    def __init__(self, region: str = "us-east-1"):
        # Handle AWS Academy session tokens
        session_token = os.getenv("AWS_SESSION_TOKEN")
        if session_token:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=session_token
            )
        else:
            self.client = boto3.client("bedrock-runtime", region_name=region)
        
        # Load model mapping from JSON
        config_path = Path(__file__).parent / "bedrock_models.json"
        with open(config_path) as f:
            config = json.load(f)
        
        self.model_map = config["model_map"]
        self.pricing = config["pricing"]
        
        # Resolve small/large model names from env vars to Bedrock IDs
        small_model = os.getenv("SMALL_MODEL_NAME", "").strip()
        large_model = os.getenv("LARGE_MODEL_NAME", "").strip()
        
        self.small_model_id = self.model_map.get(small_model) or self.model_map.get("haiku")
        self.large_model_id = self.model_map.get(large_model) or self.model_map.get("sonnet")

    def complete(self, prompt: str, model_id: str) -> CompletionResult:
        """
        Send a prompt to Bedrock and return structured result.
        
        Args:
            prompt: The text prompt to send
            model_id: Short model identifier ("haiku", "sonnet", or env var names)
            
        Returns:
            CompletionResult with response text, tokens, cost, and latency
        """
        start_time = time.time()
        
        # Resolve to actual Bedrock model ID
        if model_id == "small":
            bedrock_model_id = self.small_model_id
        elif model_id == "large":
            bedrock_model_id = self.large_model_id
        else:
            bedrock_model_id = BEDROCK_MODEL_MAP.get(model_id, model_id)
        
        # Call Bedrock Converse API
        response = self.client.converse(
            modelId=bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.0},
        )
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract response data
        response_text = response["output"]["message"]["content"][0]["text"]
        input_tokens = response["usage"]["inputTokens"]
        output_tokens = response["usage"]["outputTokens"]
        
        # Calculate cost
        cost_usd = (
            input_tokens / 1_000_000 * self.pricing[model_id]["input"] +
            output_tokens / 1_000_000 * self.pricing[model_id]["output"]
        )
        
        # Return CompletionResult
        # Note: classification, routing_reason, escalated are set by the router
        return CompletionResult(
            response=response_text,
            model_used=model_id,
            model_id=model_id,
            routing_reason="",  # Router will fill this
            escalated=False,    # Router will fill this
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            classification=None,  # Router will fill this
        )
