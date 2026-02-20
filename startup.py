import os
import sys
from dotenv import load_dotenv

REQUIRED_ENV_VARS = [
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "DD_API_KEY",
    "DD_APP_KEY",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
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
    """Confirm Datadog API key is valid."""
    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v1.api.authentication_api import AuthenticationApi
        config = Configuration()
        config.api_key["apiKeyAuth"] = os.getenv("DD_API_KEY")
        config.api_key["appKeyAuth"] = os.getenv("DD_APP_KEY")
        with ApiClient(config) as api_client:
            api = AuthenticationApi(api_client)
            result = api.validate()
        print(f"✓ Datadog reachable — valid: {result.get('valid', False)}")
    except Exception as e:
        print(f"⚠ Datadog check failed (non-fatal): {e}")


def check_neo4j():
    """Confirm Neo4j connection with a simple ping query."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )
        with driver.session() as session:
            session.run("RETURN 1 AS ping").single()
        driver.close()
        print("✓ Neo4j reachable")
    except Exception as e:
        print(f"⚠ Neo4j check failed (non-fatal): {e}")


def run():
    print("\n=== Hybrid LLM Router — Startup Checks ===\n")
    load_env()
    check_bedrock()
    check_datadog()
    check_neo4j()
    print("\n✓ All checks passed. Starting app...\n")


if __name__ == "__main__":
    run()
