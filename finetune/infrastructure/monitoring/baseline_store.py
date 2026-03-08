"""
Baseline Store for Drift Monitoring.

Stores historical metrics and label distributions for drift comparison.
"""

import json
import os
from typing import Optional
from datetime import datetime
from pathlib import Path


class BaselineStore:
    """Store and retrieve baseline metrics for drift detection."""

    def __init__(self, baseline_dir: str = "data/baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(
        self,
        name: str,
        metrics: dict,
        label_distribution: Optional[dict] = None,
        confidences: Optional[list] = None,
    ) -> str:
        """Save a baseline snapshot.

        Args:
            name: Baseline name (e.g., "v1.0", "production")
            metrics: Performance metrics dict
            label_distribution: Optional label distribution dict
            confidences: Optional list of prediction confidences

        Returns:
            Path to saved baseline
        """
        baseline = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "label_distribution": label_distribution or {},
            "confidences": confidences or [],
        }

        baseline_path = self.baseline_dir / f"{name}.json"
        with open(baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)

        # Also update "latest" symlink
        latest_path = self.baseline_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(baseline, f, indent=2)

        return str(baseline_path)

    def load_baseline(self, name: str) -> Optional[dict]:
        """Load a baseline by name.

        Args:
            name: Baseline name (e.g., "v1.0", "latest")

        Returns:
            Baseline dict or None if not found
        """
        baseline_path = self.baseline_dir / f"{name}.json"
        if not baseline_path.exists():
            return None

        with open(baseline_path, "r") as f:
            return json.load(f)

    def load_latest(self) -> Optional[dict]:
        """Load the latest baseline."""
        return self.load_baseline("latest")

    def list_baselines(self) -> list[str]:
        """List all available baselines."""
        baselines = []
        for path in self.baseline_dir.glob("*.json"):
            if path.name != "latest.json":
                baselines.append(path.stem)
        return sorted(baselines)

    def delete_baseline(self, name: str) -> bool:
        """Delete a baseline.

        Args:
            name: Baseline name

        Returns:
            True if deleted, False if not found
        """
        baseline_path = self.baseline_dir / f"{name}.json"
        if baseline_path.exists():
            baseline_path.unlink()
            return True
        return False

    def save_eval_result_as_baseline(
        self,
        version: str,
        eval_result_path: str,
        label_distribution: Optional[dict] = None,
    ) -> str:
        """Save eval result as baseline.

        Args:
            version: Version name
            eval_result_path: Path to eval_result.json
            label_distribution: Optional label distribution

        Returns:
            Path to saved baseline
        """
        with open(eval_result_path, "r") as f:
            eval_result = json.load(f)

        # Extract metrics
        metrics = {
            "accuracy": eval_result.get("accuracy", 0),
            "f1_macro": eval_result.get("f1_macro", 0),
            "f1_weighted": eval_result.get("f1_weighted", 0),
            "precision": eval_result.get("precision", 0),
            "recall": eval_result.get("recall", 0),
            "regression_pass_rate": eval_result.get("regression_pass_rate", 1.0),
            "benchmark_size": eval_result.get("benchmark_size", 0),
        }

        # Add per-class F1
        f1_per_class = eval_result.get("f1_per_class", {})
        if f1_per_class:
            metrics["f1_per_class"] = f1_per_class

        return self.save_baseline(version, metrics, label_distribution)


class DriftAlertStore:
    """Store drift alerts history."""

    def __init__(self, alerts_dir: str = "data/alerts"):
        self.alerts_dir = Path(alerts_dir)
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

    def save_alert(self, alert: dict) -> str:
        """Save a drift alert.

        Args:
            alert: Alert dict with drift details

        Returns:
            Path to saved alert
        """
        alert["timestamp"] = datetime.now().isoformat()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_type = alert.get("drift_type", "unknown")
        filename = f"{alert_type}_{timestamp}.json"

        alert_path = self.alerts_dir / filename
        with open(alert_path, "w") as f:
            json.dump(alert, f, indent=2)

        return str(alert_path)

    def get_recent_alerts(self, hours: int = 24) -> list[dict]:
        """Get recent alerts within specified hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of alert dicts
        """
        alerts = []
        cutoff = datetime.now().timestamp() - (hours * 3600)

        for path in sorted(self.alerts_dir.glob("*.json"), reverse=True):
            # Check file modification time
            if path.stat().st_mtime > cutoff:
                with open(path, "r") as f:
                    alerts.append(json.load(f))

        return alerts

    def clear_old_alerts(self, days: int = 30) -> int:
        """Clear alerts older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of alerts deleted
        """
        cutoff = datetime.now().timestamp() - (days * 86400)
        deleted = 0

        for path in self.alerts_dir.glob("*.json"):
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1

        return deleted
