"""Generate Markdown evaluation reports from EvalResult."""
import os
from datetime import datetime, timezone
from typing import Optional

from finetune.domain.entities import EvalResult
from finetune.domain.value_objects import EmotionLabel

_LABELS = [e.value for e in EmotionLabel if e != EmotionLabel.UNKNOWN]


class ReportGenerator:
    """Generate a human-readable Markdown eval report.

    Single responsibility: format EvalResult (+ optional baseline) into Markdown.
    """

    def generate(
        self,
        candidate: EvalResult,
        baseline: Optional[EvalResult] = None,
        promoted: Optional[bool] = None,
        rejection_reason: str = "",
        run_id: str = "",
    ) -> str:
        lines = [
            "# Evaluation Report",
            "",
            f"**Run ID:** {run_id or candidate.run_id}",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Benchmark size:** {candidate.benchmark_size}",
            f"**Eval time:** {candidate.eval_time_seconds:.1f}s",
            "",
        ]

        if promoted is not None:
            status = "PROMOTED" if promoted else "REJECTED"
            lines.append(f"**Decision:** {status}")
            if rejection_reason:
                lines.append(f"**Reason:** {rejection_reason}")
            lines.append("")

        lines.extend(self._metrics_table(candidate, baseline))
        lines.append("")
        lines.extend(self._per_class_table(candidate, baseline))
        lines.append("")
        lines.extend(self._confusion_matrix(candidate))
        lines.append("")
        lines.extend(self._regression_section(candidate))

        return "\n".join(lines)

    def save(self, report: str, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)

    # ------------------------------------------------------------------ #
    # Sections
    # ------------------------------------------------------------------ #

    @staticmethod
    def _metrics_table(candidate: EvalResult, baseline: Optional[EvalResult]) -> list[str]:
        lines = ["## Overall Metrics", ""]
        if baseline:
            lines.append("| Metric | Baseline | Candidate | Delta |")
            lines.append("|--------|----------|-----------|-------|")
            acc_d = candidate.accuracy - baseline.accuracy
            f1_d = candidate.f1_macro - baseline.f1_macro
            lines.append(
                f"| Accuracy | {baseline.accuracy:.4f} | {candidate.accuracy:.4f} "
                f"| {acc_d:+.4f} |"
            )
            lines.append(
                f"| F1 Macro | {baseline.f1_macro:.4f} | {candidate.f1_macro:.4f} "
                f"| {f1_d:+.4f} |"
            )
        else:
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Accuracy | {candidate.accuracy:.4f} |")
            lines.append(f"| F1 Macro | {candidate.f1_macro:.4f} |")
        return lines

    @staticmethod
    def _per_class_table(candidate: EvalResult, baseline: Optional[EvalResult]) -> list[str]:
        lines = ["## Per-Class F1", ""]
        if baseline:
            lines.append("| Class | Baseline | Candidate | Delta |")
            lines.append("|-------|----------|-----------|-------|")
            for cls in _LABELS:
                b = baseline.f1_per_class.get(cls, 0.0)
                c = candidate.f1_per_class.get(cls, 0.0)
                d = c - b
                flag = " **REGRESSION**" if d < -0.02 else ""
                lines.append(f"| {cls} | {b:.4f} | {c:.4f} | {d:+.4f}{flag} |")
        else:
            lines.append("| Class | F1 |")
            lines.append("|-------|----|")
            for cls in _LABELS:
                f1 = candidate.f1_per_class.get(cls, 0.0)
                lines.append(f"| {cls} | {f1:.4f} |")
        return lines

    @staticmethod
    def _confusion_matrix(candidate: EvalResult) -> list[str]:
        cm = candidate.confusion_matrix
        if not cm:
            return ["## Confusion Matrix", "", "_No confusion matrix data._"]

        lines = ["## Confusion Matrix", ""]
        header = "| | " + " | ".join(_LABELS) + " |"
        sep = "|---|" + "|".join(["---"] * len(_LABELS)) + "|"
        lines.append(header)
        lines.append(sep)
        for i, row in enumerate(cm):
            if i < len(_LABELS):
                label = _LABELS[i]
                cells = " | ".join(str(v) for v in row)
                lines.append(f"| **{label}** | {cells} |")
        return lines

    @staticmethod
    def _regression_section(candidate: EvalResult) -> list[str]:
        lines = ["## Regression Tests", ""]
        if candidate.regression_pass_rate > 0:
            pct = candidate.regression_pass_rate * 100
            status = "PASS" if candidate.regression_pass_rate >= 1.0 else "FAIL"
            lines.append(f"**Pass rate:** {pct:.1f}% ({status})")
        else:
            lines.append("_No regression test data._")
        return lines
