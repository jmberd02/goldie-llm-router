import boto3
import json
import time
import os
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
        self.model_map = {
            "haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Inference profile for AWS Academy
        }
        self.pricing = {
            "haiku":  {"input": 0.80,  "output": 4.00},   # per 1M tokens
            "sonnet": {"input": 3.00,  "output": 15.00},
        }

    def complete(self, prompt: str, model_id: str) -> CompletionResult:
        """
        Send a prompt to Bedrock and return structured result.
        
        Args:
            prompt: The text prompt to send
            model_id: Short model identifier ("haiku" or "sonnet")
            
        Returns:
            CompletionResult with response text, tokens, cost, and latency
        """
        start_time = time.time()
        
        # Call Bedrock Converse API
        response = self.client.converse(
            modelId=self.model_map[model_id],
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
