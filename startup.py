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


def check_ollama():
    """Fire a test call to Ollama to confirm it's running."""
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": "Say OK",
                "stream": False,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "").strip()
        print(f"✓ Ollama (qwen3:8b) reachable — response: {text[:50]!r}")
    except Exception as e:
        print(f"✗ Ollama check failed: {e}")
        print("  Make sure Ollama is running: ollama serve")
        print("  And model is pulled: ollama pull qwen3:8b")
        sys.exit(1)


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
    """Plan §4.5: if DD_API_KEY set, optionally ping Datadog (Metrics API v2); do not block on failure."""
    raw_key = os.getenv("DD_API_KEY", "")
    if not raw_key.strip():
        print("⊘ Datadog disabled (no DD_API_KEY); observability to stdout only")
        # Debug: help spot .env typos or wrong var name (never print the key value)
        dd_keys = [k for k in os.environ if k.startswith("DD_")]
        print(f"  Debug: DD_API_KEY length={len(raw_key)}; DD_* vars in env: {dd_keys or '(none)'}")
        return
    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v2.api import metrics_api
        from datadog_api_client.v2.model.metric_payload import MetricPayload
        from datadog_api_client.v2.model.metric_series import MetricSeries
        from datadog_api_client.v2.model.metric_point import MetricPoint
        from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
        import time as _time
        configuration = Configuration()
        with ApiClient(configuration) as api_client:
            api_instance = metrics_api.MetricsApi(api_client)
            body = MetricPayload(
                series=[
                    MetricSeries(
                        metric="llm_router.startup.check",
                        type=MetricIntakeType.GAUGE,
                        points=[MetricPoint(timestamp=int(_time.time()), value=1.0)],
                        tags=["service:llm_router"],
                    )
                ]
            )
            api_instance.submit_metrics(body=body)
        print("✓ Datadog enabled (metrics + logs)")
    except ImportError:
        print("⊘ Datadog disabled (datadog-api-client not installed); observability to stdout only")
    except Exception as e:
        print(f"⚠ Datadog configured but startup check failed: {e}")
        print("  Routing will continue; observability may fall back to stdout.")


def check_neo4j():
    """Neo4j integration disabled for now."""
    print("⊘ Neo4j check skipped (disabled)")


def run():
    print("\n=== Hybrid LLM Router — Startup Checks ===\n")
    load_env()
    check_ollama()
    check_bedrock()
    check_datadog()
    check_neo4j()
    print("\n✓ All checks passed. Starting app...\n")


if __name__ == "__main__":
    run()
