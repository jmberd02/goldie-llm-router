import os
import sys
from dotenv import load_dotenv

REQUIRED_ENV_VARS = [
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
]


def load_env():
    """Load .env and verify all required variables are set."""
    load_dotenv()
    missing = [k for k in REQUIRED_ENV_VARS if not os.getenv(k)]
    if missing:
        print("✗ Missing required environment variables:")
        for k in missing:
            print(f"  - {k}")
        sys.exit(1)
    print("✓ Environment variables loaded")


def check_bedrock():
    """Fire a minimal test call to Bedrock to confirm credentials and model access."""
    try:
        import boto3
        region = os.getenv("AWS_REGION", "us-east-1")
        session_token = os.getenv("AWS_SESSION_TOKEN")
        
        # Handle AWS Academy session tokens
        if session_token:
            client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=session_token
            )
        else:
            client = boto3.client("bedrock-runtime", region_name=region)
        response = client.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 8, "temperature": 0.0},
        )
        text = response["output"]["message"]["content"][0]["text"]
        print(f"✓ Bedrock (Haiku) reachable — response: {text.strip()!r}")
    except Exception as e:
        print(f"✗ Bedrock check failed: {e}")
        sys.exit(1)


def check_datadog():
    """Datadog integration disabled for now."""
    print("⊘ Datadog check skipped (disabled)")


def check_neo4j():
    """Neo4j integration disabled for now."""
    print("⊘ Neo4j check skipped (disabled)")


def run():
    print("\n=== Hybrid LLM Router — Startup Checks ===\n")
    load_env()
    check_bedrock()
    check_datadog()
    check_neo4j()
    print("\n✓ All checks passed. Starting app...\n")


if __name__ == "__main__":
    run()
