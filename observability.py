import os
from models import CompletionResult


def log_routing_decision(result: CompletionResult, prompt: str) -> None:
    """
    Log routing decision metrics to Datadog.
    Falls back to stdout if Datadog is unavailable.
    
    Args:
        result: CompletionResult containing routing decision and metrics
        prompt: Original user prompt (for context)
    """
    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v2.api.metrics_api import MetricsApi
        from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
        from datadog_api_client.v2.model.metric_payload import MetricPayload
        from datadog_api_client.v2.model.metric_point import MetricPoint
        from datadog_api_client.v2.model.metric_series import MetricSeries
        import time
        
        config = Configuration()
        config.api_key["apiKeyAuth"] = os.getenv("DD_API_KEY")
        config.api_key["appKeyAuth"] = os.getenv("DD_APP_KEY")
        
        # Build tags
        tags = [
            f"model_used:{result.model_used}",
            f"model_id:{result.model_id}",
            f"escalated:{str(result.escalated).lower()}",
        ]
        if result.classification:
            tags.append(f"task_category:{result.classification.dominant_category}")
        
        timestamp = int(time.time())
        
        # Build metric series
        series = [
            MetricSeries(
                metric="router.cost_usd",
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=result.cost_usd)],
                tags=tags,
            ),
            MetricSeries(
                metric="router.latency_ms",
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=result.latency_ms)],
                tags=tags,
            ),
            MetricSeries(
                metric="router.escalated",
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=1 if result.escalated else 0)],
                tags=tags,
            ),
            MetricSeries(
                metric="router.input_tokens",
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=result.input_tokens)],
                tags=tags,
            ),
            MetricSeries(
                metric="router.output_tokens",
                type=MetricIntakeType.GAUGE,
                points=[MetricPoint(timestamp=timestamp, value=result.output_tokens)],
                tags=tags,
            ),
        ]
        
        # Submit metrics
        with ApiClient(config) as api_client:
            api = MetricsApi(api_client)
            body = MetricPayload(series=series)
            api.submit_metrics(body=body)
            
    except Exception as e:
        # Fallback to stdout logging
        print(f"⚠ Datadog logging failed: {e}")
        _log_to_stdout(result, prompt)


def _log_to_stdout(result: CompletionResult, prompt: str) -> None:
    """Fallback stdout logging when Datadog is unavailable."""
    task_cat = result.classification.dominant_category if result.classification else "unknown"
    print(f"[METRICS] model={result.model_id} cost=${result.cost_usd:.6f} "
          f"latency={result.latency_ms:.0f}ms escalated={result.escalated} "
          f"tokens_in={result.input_tokens} tokens_out={result.output_tokens} "
          f"task={task_cat}")


def log_to_neo4j(prompt: str, result: CompletionResult) -> None:
    """
    Store routing decision as a graph in Neo4j.
    Creates: (:Request)-[:ROUTED_TO {reason, cost, latency}]->(:Model)
    
    Args:
        prompt: Original user prompt
        result: CompletionResult containing routing decision
    """
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )
        
        with driver.session() as session:
            session.run("""
                MERGE (m:Model {id: $model_id})
                CREATE (r:Request {
                    prompt_preview: $prompt_preview,
                    timestamp: datetime(),
                    cost_usd: $cost_usd,
                    latency_ms: $latency_ms,
                    escalated: $escalated,
                    task_category: $task_category
                })
                CREATE (r)-[:ROUTED_TO {
                    reason: $routing_reason,
                    difficulty: $difficulty
                }]->(m)
            """,
            model_id=result.model_id,
            prompt_preview=prompt[:100],
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            escalated=result.escalated,
            task_category=result.classification.dominant_category if result.classification else "unknown",
            routing_reason=result.routing_reason,
            difficulty=result.classification.difficulty if result.classification else 0.0,
            )
        
        driver.close()
        
    except Exception as e:
        print(f"⚠ Neo4j logging failed (non-fatal): {e}")
