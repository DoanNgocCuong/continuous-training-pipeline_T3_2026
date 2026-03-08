"""
Cost Tracker for API cost monitoring.

Tracks OpenAI API costs, token counts, and latency.
"""

import os
import time
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CostRecord:
    """Record of an API call cost."""
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    operation: str = ""


@dataclass
class CostSummary:
    """Summary of costs over a period."""
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    total_calls: int
    avg_latency_ms: float
    by_model: dict = field(default_factory=dict)


class CostTracker:
    """Track API costs and usage."""

    # Pricing per 1K tokens (USD)
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/1M in, $0.60/1M out
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4": {"input": 0.03, "output": 0.06},
    }

    def __init__(self):
        self.records: list[CostRecord] = []
        self._call_start_times: dict[str, float] = {}

    def start_call(self, call_id: str):
        """Start timing a call."""
        self._call_start_times[call_id] = time.time()

    def end_call(self, call_id: str, model: str, input_tokens: int,
                 output_tokens: int, operation: str = "") -> CostRecord:
        """End timing a call and record cost."""
        start_time = self._call_start_times.pop(call_id, time.time())
        latency_ms = (time.time() - start_time) * 1000

        cost = self._calculate_cost(model, input_tokens, output_tokens)

        record = CostRecord(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            operation=operation,
        )
        self.records.append(record)
        return record

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        pricing = self.PRICING.get(model, self.PRICING["gpt-4o-mini"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    def get_summary(self) -> CostSummary:
        """Get summary of all recorded costs."""
        if not self.records:
            return CostSummary(
                total_cost_usd=0.0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_calls=0,
                avg_latency_ms=0.0,
            )

        total_cost = sum(r.cost_usd for r in self.records)
        total_input = sum(r.input_tokens for r in self.records)
        total_output = sum(r.output_tokens for r in self.records)
        total_calls = len(self.records)
        avg_latency = sum(r.latency_ms for r in self.records) / total_calls

        # Group by model
        by_model = {}
        for r in self.records:
            if r.model not in by_model:
                by_model[r.model] = {
                    "cost": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "calls": 0,
                }
            by_model[r.model]["cost"] += r.cost_usd
            by_model[r.model]["input_tokens"] += r.input_tokens
            by_model[r.model]["output_tokens"] += r.output_tokens
            by_model[r.model]["calls"] += 1

        return CostSummary(
            total_cost_usd=total_cost,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_calls=total_calls,
            avg_latency_ms=avg_latency,
            by_model=by_model,
        )

    def reset(self):
        """Reset all records."""
        self.records.clear()
        self._call_start_times.clear()

    def to_dict(self) -> dict:
        """Export to dictionary."""
        summary = self.get_summary()
        return {
            "total_cost_usd": summary.total_cost_usd,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_calls": summary.total_calls,
            "avg_latency_ms": summary.avg_latency_ms,
            "by_model": summary.by_model,
            "records": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "model": r.model,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "cost_usd": r.cost_usd,
                    "latency_ms": r.latency_ms,
                    "operation": r.operation,
                }
                for r in self.records
            ],
        }


# Singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
