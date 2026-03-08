"""
Health Checker for Canary Deployment.

Monitors service health: error rate, latency, availability.
"""

import time
import urllib.request
import urllib.error
import json
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthMetrics:
    """Health metrics from a check."""
    status: HealthStatus
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    availability: float
    details: dict


class HealthChecker:
    """Check service health for canary deployment."""

    def __init__(
        self,
        health_endpoint: str = "http://localhost:8000/health",
        metrics_endpoint: str = "http://localhost:8000/metrics",
        check_interval: int = 30,
        timeout: int = 10,
    ):
        self.health_endpoint = health_endpoint
        self.metrics_endpoint = metrics_endpoint
        self.check_interval = check_interval
        self.timeout = timeout
        self._history: list[HealthMetrics] = []

    def check_health(self) -> HealthStatus:
        """Check basic health endpoint.

        Returns:
            HealthStatus enum
        """
        try:
            req = urllib.request.Request(self.health_endpoint)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return HealthStatus.HEALTHY
                else:
                    return HealthStatus.UNHEALTHY
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            return HealthStatus.UNHEALTHY

    def get_metrics(self) -> Optional[dict]:
        """Get detailed metrics from metrics endpoint.

        Returns:
            Metrics dict or None if unavailable
        """
        try:
            req = urllib.request.Request(self.metrics_endpoint)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return json.loads(response.read())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            pass
        return None

    def check(
        self,
        error_rate_threshold: float = 1.0,
        latency_p95_threshold: float = 500,
        availability_threshold: float = 99.0,
    ) -> HealthMetrics:
        """Perform full health check.

        Args:
            error_rate_threshold: Max error rate percentage
            latency_p95_threshold: Max p95 latency in ms
            availability_threshold: Min availability percentage

        Returns:
            HealthMetrics with status
        """
        # Check basic health
        health_status = self.check_health()

        # Get detailed metrics
        metrics = self.get_metrics()

        if metrics is None:
            # Can't get metrics - assume unhealthy
            result = HealthMetrics(
                status=HealthStatus.UNHEALTHY,
                error_rate=100.0,
                latency_p50=0,
                latency_p95=0,
                latency_p99=0,
                availability=0,
                details={"error": "Could not fetch metrics"},
            )
        else:
            # Extract metrics
            error_rate = metrics.get("error_rate", 0)
            latency_p50 = metrics.get("latency_p50", 0)
            latency_p95 = metrics.get("latency_p95", 0)
            latency_p99 = metrics.get("latency_p99", 0)
            availability = metrics.get("availability", 100)

            # Determine status
            status = HealthStatus.HEALTHY
            if (error_rate > error_rate_threshold or
                latency_p95 > latency_p95_threshold or
                availability < availability_threshold):
                status = HealthStatus.UNHEALTHY
            elif (error_rate > error_rate_threshold * 0.5 or
                  latency_p95 > latency_p95_threshold * 0.5):
                status = HealthStatus.DEGRADED

            result = HealthMetrics(
                status=status,
                error_rate=error_rate,
                latency_p50=latency_p50,
                latency_p95=latency_p95,
                latency_p99=latency_p99,
                availability=availability,
                details=metrics,
            )

        self._history.append(result)
        return result

    def wait_for_healthy(
        self,
        success_threshold: int = 3,
        failure_threshold: int = 3,
        **thresholds,
    ) -> bool:
        """Wait for service to become healthy.

        Args:
            success_threshold: Consecutive successes needed
            failure_threshold: Consecutive failures before giving up
            **thresholds: Thresholds for check()

        Returns:
            True if service became healthy, False if failed
        """
        consecutive_successes = 0
        consecutive_failures = 0

        while True:
            result = self.check(**thresholds)

            if result.status == HealthStatus.HEALTHY:
                consecutive_successes += 1
                consecutive_failures = 0
                if consecutive_successes >= success_threshold:
                    return True
            else:
                consecutive_failures += 1
                consecutive_successes = 0
                if consecutive_failures >= failure_threshold:
                    return False

            time.sleep(self.check_interval)

    def get_history(self) -> list[HealthMetrics]:
        """Get health check history."""
        return self._history.copy()

    def clear_history(self):
        """Clear health check history."""
        self._history.clear()


def check_model_inference(
    model_endpoint: str,
    test_inputs: list[str],
    expected_labels: list[str],
) -> dict:
    """Check model inference quality.

    Args:
        model_endpoint: Inference endpoint URL
        test_inputs: List of test input texts
        expected_labels: Expected labels for inputs

    Returns:
        Dict with accuracy and latency metrics
    """
    correct = 0
    latencies = []

    for text, expected in zip(test_inputs, expected_labels):
        start = time.time()

        try:
            req = urllib.request.Request(
                model_endpoint,
                data=json.dumps({"text": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read())
                predicted = result.get("label", "")

                if predicted.lower() == expected.lower():
                    correct += 1
        except Exception:
            pass

        latencies.append((time.time() - start) * 1000)  # ms

    import numpy as np
    accuracy = correct / len(test_inputs) if test_inputs else 0

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": len(test_inputs),
        "latency_p50": float(np.percentile(latencies, 50)) if latencies else 0,
        "latency_p95": float(np.percentile(latencies, 95)) if latencies else 0,
        "latency_p99": float(np.percentile(latencies, 99)) if latencies else 0,
    }
