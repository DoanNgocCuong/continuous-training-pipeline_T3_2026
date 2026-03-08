"""
Data Drift Detector Service.

Detects drift in label distribution using KL divergence, PSI, and chi-squared tests.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class DriftResult:
    """Result of drift detection."""
    metric: str
    value: float
    threshold: float
    has_drift: bool
    details: Optional[dict] = None


class DataDriftDetector:
    """Detect drift in label distribution."""

    def __init__(
        self,
        kl_threshold: float = 0.1,
        psi_threshold: float = 0.25,
        chi2_pvalue_threshold: float = 0.05,
    ):
        self.kl_threshold = kl_threshold
        self.psi_threshold = psi_threshold
        self.chi2_pvalue_threshold = chi2_pvalue_threshold

    def detect(
        self,
        baseline_distribution: dict[str, float],
        current_distribution: dict[str, float],
    ) -> list[DriftResult]:
        """Detect drift between baseline and current distributions.

        Args:
            baseline_distribution: Dict of label -> probability (baseline)
            current_distribution: Dict of label -> probability (current)

        Returns:
            List of DriftResult for each metric
        """
        results = []

        # Get all labels (union)
        all_labels = set(baseline_distribution.keys()) | set(current_distribution.keys())

        # Align distributions
        baseline = np.array([baseline_distribution.get(l, 0.0) for l in sorted(all_labels)])
        current = np.array([current_distribution.get(l, 0.0) for l in sorted(all_labels)])

        # KL Divergence
        kl_result = self._kl_divergence(baseline, current)
        results.append(kl_result)

        # PSI
        psi_result = self._psi(baseline, current)
        results.append(psi_result)

        # Chi-squared test
        chi2_result = self._chi2_test(baseline, current)
        results.append(chi2_result)

        return results

    def _kl_divergence(self, baseline: np.ndarray, current: np.ndarray) -> DriftResult:
        """Calculate KL Divergence D(P||Q)."""
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        baseline = baseline + epsilon
        current = current + epsilon

        # Normalize
        baseline = baseline / baseline.sum()
        current = current / current.sum()

        # KL Divergence: sum(P * log(P/Q))
        kl = np.sum(baseline * np.log(baseline / current))

        return DriftResult(
            metric="kl_divergence",
            value=kl,
            threshold=self.kl_threshold,
            has_drift=kl > self.kl_threshold,
            details={
                "interpretation": "Higher values indicate more distribution shift",
                "baseline": baseline.tolist(),
                "current": current.tolist(),
            },
        )

    def _psi(self, baseline: np.ndarray, current: np.ndarray) -> DriftResult:
        """Calculate Population Stability Index (PSI)."""
        epsilon = 1e-10
        baseline = baseline + epsilon
        current = current + epsilon

        # Normalize
        baseline = baseline / baseline.sum()
        current = current / current.sum()

        # PSI = sum((current - baseline) * log(current/baseline))
        psi = np.sum((current - baseline) * np.log(current / baseline))

        return DriftResult(
            metric="psi",
            value=psi,
            threshold=self.psi_threshold,
            has_drift=psi > self.psi_threshold,
            details={
                "interpretation": "< 0.1: no change, 0.1-0.2: some change, > 0.2: major shift",
            },
        )

    def _chi2_test(self, baseline: np.ndarray, current: np.ndarray) -> DriftResult:
        """Perform chi-squared test for distribution equality."""
        from scipy import stats

        # Normalize to counts (assume 1000 samples)
        baseline_counts = baseline / baseline.sum() * 1000
        current_counts = current / current.sum() * 1000

        # Chi-squared test
        chi2, pvalue = stats.chisquare(current_counts, f_exp=baseline_counts)

        return DriftResult(
            metric="chi2_pvalue",
            value=pvalue,
            threshold=self.chi2_pvalue_threshold,
            has_drift=pvalue < self.chi2_pvalue_threshold,
            details={
                "chi2_statistic": float(chi2),
                "interpretation": "Low p-value suggests significant difference",
            },
        )

    def detect_confidence_drift(
        self,
        baseline_confidences: list[float],
        current_confidences: list[float],
        mean_drop_threshold: float = 0.1,
        std_increase_threshold: float = 0.2,
    ) -> list[DriftResult]:
        """Detect drift in prediction confidence."""
        results = []

        baseline_mean = np.mean(baseline_confidences)
        current_mean = np.mean(current_confidences)
        mean_drop = baseline_mean - current_mean

        results.append(DriftResult(
            metric="mean_confidence_drop",
            value=mean_drop / baseline_mean if baseline_mean > 0 else 0,
            threshold=mean_drop_threshold,
            has_drift=mean_drop / baseline_mean > mean_drop_threshold if baseline_mean > 0 else False,
            details={
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
            },
        ))

        baseline_std = np.std(baseline_confidences)
        current_std = np.std(current_confidences)
        std_increase = (current_std - baseline_std) / baseline_std if baseline_std > 0 else 0

        results.append(DriftResult(
            metric="std_confidence_increase",
            value=std_increase,
            threshold=std_increase_threshold,
            has_drift=std_increase > std_increase_threshold,
            details={
                "baseline_std": baseline_std,
                "current_std": current_std,
            },
        ))

        return results
