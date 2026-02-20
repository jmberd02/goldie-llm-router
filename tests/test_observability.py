"""
Unit tests for observability (plan §4.6).
Mock Datadog HTTP and client; assert no exception; assert metric series and log payload
(correct tags, no prompt text in log body).
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from models import CompletionResult, Classification


def _make_result(
    model_used: str = "small",
    model_id: str = "qwen2.5:1.5b",
    escalated: bool = False,
    task_category: str = "general_qa",
    difficulty: float = 0.2,
) -> CompletionResult:
    return CompletionResult(
        response="test response",
        model_used=model_used,
        model_id=model_id,
        routing_reason="score ok",
        escalated=escalated,
        input_tokens=10,
        output_tokens=20,
        cost_usd=0.0,
        latency_ms=100.0,
        classification=Classification(
            subtasks=["look up fact"],
            task_categories={task_category: 0.9},
            difficulty=difficulty,
            dominant_category=task_category,
            escalate=escalated,
        ),
    )


class TestObservabilityStdoutOnly(unittest.TestCase):
    """With DD_API_KEY unset, log_routing_decision must not raise and must not call Datadog."""

    @patch.dict(os.environ, {"DD_API_KEY": ""}, clear=False)
    def test_stdout_only_no_exception(self):
        import observability
        observability._dd_initialized = None  # reset lazy init
        result = _make_result()
        try:
            observability.log_routing_decision(result, "What is 2+2?")
        except Exception as e:
            self.fail(f"log_routing_decision raised: {e}")

    @patch.dict(os.environ, {"DD_API_KEY": ""}, clear=False)
    @patch("observability._submit_metrics")
    @patch("observability._submit_log")
    def test_stdout_only_datadog_not_called(self, mock_log, mock_metrics):
        import observability
        observability._dd_initialized = None
        result = _make_result()
        observability.log_routing_decision(result, "Hello")
        mock_metrics.assert_not_called()
        mock_log.assert_not_called()


class TestObservabilityWithDatadogMocks(unittest.TestCase):
    """With DD_API_KEY set, assert metrics and log payloads (tags, no PII)."""

    @patch.dict(os.environ, {"DD_API_KEY": "fake_key", "DD_SERVICE": "llm_router"}, clear=False)
    @patch("observability._submit_metrics")
    @patch("observability._submit_log")
    def test_datadog_path_called_no_exception(self, mock_log, mock_metrics):
        import observability
        observability._dd_initialized = None
        result = _make_result(model_used="large", escalated=True, task_category="agentic_tool_use")
        prompt = "Check calendar and set reminder"
        observability.log_routing_decision(result, prompt)
        mock_metrics.assert_called_once()
        mock_log.assert_called_once()
        # Log must receive result and prompt; we assert no prompt text in payload in next test
        args = mock_log.call_args[0]
        self.assertEqual(args[0], result)
        self.assertEqual(args[1], prompt)

    @patch.dict(os.environ, {"DD_API_KEY": "fake_key"}, clear=False)
    def test_submit_log_does_not_contain_prompt_text(self):
        """Plan §4.6: assert no prompt text in log body (no PII)."""
        try:
            import requests
        except ImportError:
            self.skipTest("requests not installed")
        import observability
        observability._dd_initialized = None
        result = _make_result()
        secret = "my-secret-prompt-content-12345"
        with patch.object(requests, "post", MagicMock()) as mock_post:
            observability._submit_log(result, secret)
        self.assertEqual(mock_post.call_count, 1)
        body = mock_post.call_args[1]["json"]
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)
        log_entry = body[0]
        # Must not contain the actual prompt
        self.assertNotIn(secret, str(log_entry))
        # Must contain prompt_length for analysis (plan §3.2)
        self.assertEqual(log_entry.get("prompt_length"), len(secret))

    def test_submit_metrics_uses_bounded_tags(self):
        """Plan §3.1, §4.6: metric series must use bounded tags (model_used, task_category, escalated)."""
        try:
            from datadog_api_client.v2.api import metrics_api
        except ImportError:
            self.skipTest("datadog-api-client not installed")
        import observability
        observability._dd_initialized = None
        result = _make_result(model_used="small", task_category="math", escalated=False)
        with patch("datadog_api_client.v2.api.metrics_api.MetricsApi") as mock_metrics_api_class:
            with patch("datadog_api_client.ApiClient"):
                with patch("datadog_api_client.Configuration"):
                    mock_instance = MagicMock()
                    mock_metrics_api_class.return_value = mock_instance
                    observability._submit_metrics(result, "What is 2+2?")
        submit_call = mock_instance.submit_metrics.call_args
        self.assertIsNotNone(submit_call)
        body = submit_call[1]["body"]
        series = body.series
        self.assertGreater(len(series), 0)
        bounded_values = {"small", "large", "true", "false", "general_qa", "code_operation",
                          "multi_step_reasoning", "agentic_tool_use", "long_context", "math", "unknown"}
        for s in series:
            for tag in getattr(s, "tags", []) or []:
                if ":" in tag:
                    _, val = tag.split(":", 1)
                    self.assertIn(val.lower(), bounded_values, msg=f"High-cardinality tag? {tag}")


if __name__ == "__main__":
    unittest.main()
