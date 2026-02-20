"""
Observability for the hybrid LLM router: stdout fallback + optional Datadog (metrics + logs).

Uses Option B — HTTP API: Metrics API v2 for metrics, HTTP Logs Intake for logs (plan §4.2, §4.4).
When DD_API_KEY is set, each routing decision is sent to Datadog (plan §4.1). Otherwise stdout only.
Failures in Datadog are caught and logged to stderr; the request never fails (plan §4.3).
"""

import os
import sys
import time
from typing import Optional

from models import CompletionResult

# Plan §3.1: bounded tag values only to avoid high-cardinality metrics billing
VALID_TASK_CATEGORIES = frozenset({
    "general_qa",
    "code_operation",
    "multi_step_reasoning",
    "agentic_tool_use",
    "long_context",
    "math",
})

# Plan §4.2: lazy init so missing DD_API_KEY doesn't require client library
_dd_initialized: Optional[bool] = None


def _is_datadog_enabled() -> bool:
    """Return True if DD_API_KEY is set and non-empty (plan §4.1)."""
    global _dd_initialized
    if _dd_initialized is None:
        _dd_initialized = bool(os.environ.get("DD_API_KEY", "").strip())
    return _dd_initialized


def _get_base_tags() -> list[str]:
    """Unified service tagging: env, service (plan §1.3, §3.1)."""
    tags = []
    env = os.environ.get("DD_ENV", "").strip()
    if env:
        tags.append(f"env:{env}")
    service = os.environ.get("DD_SERVICE", "llm_router").strip()
    tags.append(f"service:{service}")
    return tags


def _normalize_task_category(classification: Optional[object]) -> str:
    """Return a bounded task_category for tagging."""
    if classification is None:
        return "unknown"
    cat = getattr(classification, "dominant_category", None) or "unknown"
    if isinstance(cat, str) and cat in VALID_TASK_CATEGORIES:
        return cat
    return "unknown"


def _log_to_stdout(result: CompletionResult, prompt: str) -> None:
    """Always run: stdout fallback (plan §4.2 public API step 1)."""
    task_cat = result.classification.dominant_category if result.classification else "unknown"
    print(
        f"[METRICS] model={result.model_id} cost=${result.cost_usd:.6f} "
        f"latency={result.latency_ms:.0f}ms escalated={result.escalated} "
        f"tokens_in={result.input_tokens} tokens_out={result.output_tokens} "
        f"task={task_cat}"
    )


def _submit_metrics(result: CompletionResult, prompt: str) -> None:
    """Submit metrics via Metrics API v2 (Option B — HTTP API). Plan §3.1, §4.2, §4.4."""
    if not _is_datadog_enabled():
        return
    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v2.api import metrics_api
        from datadog_api_client.v2.model.metric_payload import MetricPayload
        from datadog_api_client.v2.model.metric_series import MetricSeries
        from datadog_api_client.v2.model.metric_point import MetricPoint
        from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
    except ImportError:
        print("[observability] datadog-api-client not installed; skipping metrics", file=sys.stderr)
        return

    task_cat = _normalize_task_category(result.classification)
    base = _get_base_tags()
    model_used = result.model_used  # "small" | "large" — bounded (§3.1)
    escalated = "true" if result.escalated else "false"
    ts = int(time.time())

    tags_request = base + [
        f"model_used:{model_used}",
        f"task_category:{task_cat}",
        f"escalated:{escalated}",
    ]

    # Plan §3.1 table: llm_router.requests.count, latency_ms, cost_usd, tokens, difficulty
    series = [
        MetricSeries(
            metric="llm_router.requests.count",
            type=MetricIntakeType.COUNT,
            points=[MetricPoint(timestamp=ts, value=1.0)],
            tags=tags_request,
        ),
        # End-to-end latency (ms)
        MetricSeries(
            metric="llm_router.latency_ms",
            type=MetricIntakeType.GAUGE,
            points=[MetricPoint(timestamp=ts, value=float(result.latency_ms))],
            tags=tags_request,
        ),
        # Cost (USD) per request
        MetricSeries(
            metric="llm_router.cost_usd",
            type=MetricIntakeType.GAUGE,
            points=[MetricPoint(timestamp=ts, value=result.cost_usd)],
            tags=base + [f"model_used:{model_used}", f"escalated:{escalated}"],
        ),
        # Tokens
        MetricSeries(
            metric="llm_router.tokens.input",
            type=MetricIntakeType.COUNT,
            points=[MetricPoint(timestamp=ts, value=float(result.input_tokens))],
            tags=base + [f"model_used:{model_used}"],
        ),
        MetricSeries(
            metric="llm_router.tokens.output",
            type=MetricIntakeType.COUNT,
            points=[MetricPoint(timestamp=ts, value=float(result.output_tokens))],
            tags=base + [f"model_used:{model_used}"],
        ),
    ]

    # Classification difficulty (for calibration); only when classification exists
    if result.classification is not None:
        difficulty = getattr(result.classification, "difficulty", None)
        if difficulty is not None:
            series.append(
                MetricSeries(
                    metric="llm_router.classification.difficulty",
                    type=MetricIntakeType.GAUGE,
                    points=[MetricPoint(timestamp=ts, value=float(difficulty))],
                    tags=base + [f"task_category:{task_cat}"],
                )
            )

    body = MetricPayload(series=series)
    try:
        configuration = Configuration()  # reads DD_API_KEY, DD_APP_KEY, DD_SITE from env (§4.1)
        with ApiClient(configuration) as api_client:
            api_instance = metrics_api.MetricsApi(api_client)
            api_instance.submit_metrics(body=body)
    except Exception as e:
        print(f"[observability] Datadog metrics error: {e}", file=sys.stderr)  # §4.3 non-blocking


def _submit_log(result: CompletionResult, prompt: str) -> None:
    """Submit one structured log via HTTP Logs Intake (Option B). Plan §3.2, §4.2. No PII (§5)."""
    if not _is_datadog_enabled():
        return
    api_key = os.environ.get("DD_API_KEY", "").strip()
    if not api_key:
        return
    site = os.environ.get("DD_SITE", "datadoghq.com").strip().replace("https://", "").split("/")[0]
    service = os.environ.get("DD_SERVICE", "llm_router").strip()
    task_cat = _normalize_task_category(result.classification)
    model_used = result.model_used
    model_name = (result.model_id or "").replace(",", "_")  # actual model name for filtering
    escalated = "true" if result.escalated else "false"

    # Short human-readable message (indexed for search)
    message = (
        f"llm_router request routed to {model_used} model"
        f" (task={task_cat}, escalated={escalated})"
    )
    ddtags = f"service:{service},model_used:{model_used},model:{model_name},task_category:{task_cat},escalated:{escalated}"
    env = os.environ.get("DD_ENV", "").strip()
    if env:
        ddtags += f",env:{env}"

    log_body = {
        "message": message,
        "service": service,
        "ddsource": "python",
        "ddtags": ddtags,
        # Structured attributes (filterable; no PII)
        "model_id": result.model_id,
        "model_used": model_used,
        "routing_reason": result.routing_reason,
        "escalated": result.escalated,
        "cost_usd": result.cost_usd,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "task_category": task_cat,
        "prompt_length": len(prompt),
    }
    if result.classification is not None:
        log_body["difficulty"] = getattr(result.classification, "difficulty", None)
        log_body["dominant_category"] = getattr(result.classification, "dominant_category", None)

    url = f"https://http-intake.logs.{site}/v1/input"  # plan §4.2 HTTP intake URL
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
    }
    try:
        import requests
        resp = requests.post(
            url,
            json=[log_body],
            headers=headers,
            timeout=5,  # plan §4.3 short timeout so app doesn't hang
        )
        if resp.status_code >= 400:
            print(
                f"[observability] Datadog logs intake error: {resp.status_code} {resp.text[:200]}",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"[observability] Datadog logs error: {e}", file=sys.stderr)


def log_routing_decision(result: CompletionResult, prompt: str) -> None:
    """
    Single entry point for observability (plan §4.2).
    (1) Always stdout; (2) if DD_API_KEY set, submit metrics then log; exceptions caught (§4.3).
    """
    _log_to_stdout(result, prompt)
    if _is_datadog_enabled():
        try:
            _submit_metrics(result, prompt)
        except Exception as e:
            print(f"[observability] Datadog metrics failed: {e}", file=sys.stderr)
        try:
            _submit_log(result, prompt)
        except Exception as e:
            print(f"[observability] Datadog log failed: {e}", file=sys.stderr)


def log_to_neo4j(prompt: str, result: CompletionResult) -> None:
    """
    Store routing decision as a graph in Neo4j.
    (Neo4j integration disabled for now)
    """
    pass
