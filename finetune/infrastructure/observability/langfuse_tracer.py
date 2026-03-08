"""
Langfuse Tracer for observability.

Provides tracing for pipeline steps: labeling, training, evaluation.
"""

from typing import Optional
from functools import wraps
import os

# Lazy import to avoid startup overhead
_langfuse = None


def _get_langfuse():
    """Lazy load langfuse to avoid import overhead."""
    global _langfuse
    if _langfuse is None:
        try:
            from langfuse import Langfuse
            _langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        except ImportError:
            _langfuse = None
    return _langfuse


def is_enabled() -> bool:
    """Check if Langfuse is enabled."""
    return os.getenv("LANGFUSE_ENABLED", "true").lower() == "true" and _get_langfuse() is not None


class LangfuseTracer:
    """Tracer for Langfuse observability."""

    def __init__(self, service_name: str = "emotion-ct-pipeline", version: str = "v1.0"):
        self.service_name = service_name
        self.version = version
        self._langfuse = _get_langfuse()

    def trace_generation(self, name: str):
        """Context manager for tracing a generation."""
        if not is_enabled():
            return _NoOpContext()

        return self._langfuse.trace(
            name=name,
            metadata={
                "service": self.service_name,
                "version": self.version,
            }
        )

    def trace_event(self, name: str, **kwargs):
        """Trace a single event."""
        if not is_enabled():
            return

        if self._langfuse:
            self._langfuse.trace(
                name=name,
                metadata={**kwargs, "service": self.service_name, "version": self.version}
            )

    def log_completion(self, name: str, input_text: str, output_text: str,
                      model: str, tokens: Optional[dict] = None, **kwargs):
        """Log a completion (LLM call)."""
        if not is_enabled():
            return

        if self._langfuse:
            self._langfuse.completion_new(
                name=name,
                input=input_text,
                output=output_text,
                model=model,
                tokens=tokens or {},
                metadata={**kwargs, "service": self.service_name, "version": self.version}
            )

    def log_cost(self, cost: float, model: str, tokens: dict):
        """Log API cost."""
        if not is_enabled():
            return

        if self._langfuse:
            self._langfuse.trace(
                name=f"cost:{model}",
                metadata={
                    "cost_usd": cost,
                    "tokens": tokens,
                    "service": self.service_name,
                    "version": self.version,
                }
            )


def trace(name: str, **metadata):
    """Decorator for tracing function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = LangfuseTracer()
            with tracer.trace_generation(name) as trace:
                try:
                    result = func(*args, **kwargs)
                    if trace:
                        trace.generation(
                            input=str(args)[:500],
                            output=str(result)[:500],
                        )
                    return result
                except Exception as e:
                    if trace:
                        trace.update(metadata={"error": str(e)})
                    raise
        return wrapper
    return decorator


class _NoOpContext:
    """No-op context manager for when Langfuse is disabled."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


# Singleton instance
_default_tracer: Optional[LangfuseTracer] = None


def get_tracer() -> LangfuseTracer:
    """Get the default tracer instance."""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = LangfuseTracer()
    return _default_tracer
