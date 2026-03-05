from dataclasses import dataclass

from ..entities import EvalResult


@dataclass
class PromotionPolicy:
    min_accuracy_improvement: float = 0.005   # +0.5%
    min_f1_improvement: float = 0.003         # +0.3%
    max_per_class_regression: float = 0.02    # -2%
    min_regression_pass_rate: float = 1.0     # 100%
    min_test_set_size: int = 500


class PromotionDeciderService:

    def __init__(self, policy: PromotionPolicy):
        self.policy = policy

    def decide(
        self,
        candidate: EvalResult,
        baseline: EvalResult,
    ) -> tuple[bool, str]:
        """Returns (should_promote, reason)."""
        p = self.policy

        acc_diff = candidate.accuracy - baseline.accuracy
        if acc_diff < p.min_accuracy_improvement:
            return False, (
                f"Accuracy +{acc_diff:.4f} < threshold +{p.min_accuracy_improvement}"
            )

        f1_diff = candidate.f1_macro - baseline.f1_macro
        if f1_diff < p.min_f1_improvement:
            return False, (
                f"F1 macro +{f1_diff:.4f} < threshold +{p.min_f1_improvement}"
            )

        for cls, f1 in candidate.f1_per_class.items():
            baseline_f1 = baseline.f1_per_class.get(cls, 0)
            drop = baseline_f1 - f1
            if drop > p.max_per_class_regression:
                return False, (
                    f"Class '{cls}' F1 dropped {drop:.4f} > max {p.max_per_class_regression}"
                )

        if candidate.regression_pass_rate < p.min_regression_pass_rate:
            return False, (
                f"Regression pass {candidate.regression_pass_rate:.0%} "
                f"< required {p.min_regression_pass_rate:.0%}"
            )

        if candidate.benchmark_size < p.min_test_set_size:
            return False, (
                f"Test set {candidate.benchmark_size} < min {p.min_test_set_size}"
            )

        return True, "All criteria passed"
