"""
Performance Drift Detector Service.

Detects drift in model performance metrics (accuracy, F1, latency).
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceDriftResult:
    """Result of performance drift detection."""
    metric: str
    current_value: float
    baseline_value: float
    absolute_change: float
    relative_change: float
    threshold: float
    has_drift: bool


class PerformanceDriftDetector:
    """Detect drift in model performance metrics."""

    def __init__(
        self,
        accuracy_drop_threshold: float = 0.05,
        f1_drop_threshold: float = 0.03,
        per_class_drop_threshold: float = 0.05,
        latency_increase_threshold: float = 0.20,
    ):
        self.accuracy_drop_threshold = accuracy_drop_threshold
        self.f1_drop_threshold = f1_drop_threshold
        self.per_class_drop_threshold = per_class_drop_threshold
        self.latency_increase_threshold = latency_increase_threshold

    def detect(
        self,
        baseline_metrics: dict,
        current_metrics: dict,
    ) -> list[PerformanceDriftResult]:
        """Detect performance drift between baseline and current metrics.

        Args:
            baseline_metrics: Dict of metric name -> value (baseline)
            current_metrics: Dict of metric name -> value (current)

        Returns:
            List of PerformanceDriftResult for each metric
        """
        results = []

        # Accuracy drift
        if "accuracy" in baseline_metrics and "accuracy" in current_metrics:
            results.append(self._detect_metric_drift(
                "accuracy",
                baseline_metrics["accuracy"],
                current_metrics["accuracy"],
                self.accuracy_drop_threshold,
            ))

        # F1 Macro drift
        if "f1_macro" in baseline_metrics and "f1_macro" in current_metrics:
            results.append(self._detect_metric_drift(
                "f1_macro",
                baseline_metrics["f1_macro"],
                current_metrics["f1_macro"],
                self.f1_drop_threshold,
            ))

        # Per-class F1 drift
        if "f1_per_class" in baseline_metrics and "f1_per_class" in current_metrics:
            per_class_results = self._detect_per_class_drift(
                baseline_metrics["f1_per_class"],
                current_metrics["f1_per_class"],
            )
            results.extend(per_class_results)

        # Latency drift
        if "latency_p95" in baseline_metrics and "latency_p95" in current_metrics:
            results.append(self._detect_metric_drift(
                "latency_p95",
                baseline_metrics["latency_p95"],
                current_metrics["latency_p95"],
                self.latency_increase_threshold,
                is_increase_bad=True,
            ))

        if "latency_p99" in baseline_metrics and "latency_p99" in current_metrics:
            results.append(self._detect_metric_drift(
                "latency_p99",
                baseline_metrics["latency_p99"],
                current_metrics["latency_p99"],
                self.latency_increase_threshold * 1.5,  # 30% for p99
                is_increase_bad=True,
            ))

        return results

    def _detect_metric_drift(
        self,
        metric_name: str,
        baseline_value: float,
        current_value: float,
        threshold: float,
        is_increase_bad: bool = False,
    ) -> PerformanceDriftResult:
        """Detect drift for a single metric."""
        absolute_change = current_value - baseline_value
        relative_change = absolute_change / baseline_value if baseline_value != 0 else 0

        if is_increase_bad:
            # For latency, increase is bad (threshold exceeded means drift)
            has_drift = relative_change > threshold
        else:
            # For accuracy/F1, decrease is bad
            has_drift = absolute_change < -threshold

        return PerformanceDriftResult(
            metric=metric_name,
            current_value=current_value,
            baseline_value=baseline_value,
            absolute_change=absolute_change,
            relative_change=relative_change,
            threshold=threshold,
            has_drift=has_drift,
        )

    def _detect_per_class_drift(
        self,
        baseline_f1: dict[str, float],
        current_f1: dict[str, float],
    ) -> list[PerformanceDriftResult]:
        """Detect per-class F1 drift."""
        results = []

        all_classes = set(baseline_f1.keys()) | set(current_f1.keys())

        for emotion in all_classes:
            baseline = baseline_f1.get(emotion, 0)
            current = current_f1.get(emotion, 0)

            results.append(self._detect_metric_drift(
                f"f1_{emotion}",
                baseline,
                current,
                self.per_class_drop_threshold,
            ))

        return results

    def get_regression_pass_rate(
        self,
        drift_results: list[PerformanceDriftResult],
    ) -> float:
        """Calculate regression pass rate from drift results.

        Args:
            drift_results: List of drift detection results

        Returns:
            Pass rate (0-1) - percentage of metrics without drift
        """
        if not drift_results:
            return 1.0

        passing = sum(1 for r in drift_results if not r.has_drift)
        return passing / len(drift_results)

    def get_violations(
        self,
        drift_results: list[PerformanceDriftResult],
    ) -> list[dict]:
        """Get list of metrics that have drifted.

        Args:
            drift_results: List of drift detection results

        Returns:
            List of dicts with drift details
        """
        violations = []
        for r in drift_results:
            if r.has_drift:
                violations.append({
                    "metric": r.metric,
                    "baseline": r.baseline_value,
                    "current": r.current_value,
                    "change": r.absolute_change,
                    "threshold": r.threshold,
                })
        return violations


class PerformanceHistory:
    """Track historical performance metrics."""

    def __init__(self):
        self.history: list[dict] = []

    def add(
        self,
        timestamp: datetime,
        metrics: dict,
        version: str,
    ) -> None:
        """Add a performance record."""
        self.history.append({
            "timestamp": timestamp.isoformat(),
            "version": version,
            "metrics": metrics,
        })

    def get_baseline(self, n: int = 5) -> Optional[dict]:
        """Get baseline metrics (average of last n runs)."""
        if len(self.history) < n:
            return None

        recent = self.history[-n:]
        baseline = {}

        # Average each metric
        all_metrics = set()
        for record in recent:
            all_metrics.update(record["metrics"].keys())

        for metric in all_metrics:
            values = [r["metrics"].get(metric, 0) for r in recent]
            baseline[metric] = np.mean(values)

        return baseline

    def get_trend(
        self,
        metric_name: str,
        window: int = 10,
    ) -> list[float]:
        """Get trend for a specific metric."""
        values = []
        for record in self.history[-window:]:
            if metric_name in record["metrics"]:
                values.append(record["metrics"][metric_name])
        return values
