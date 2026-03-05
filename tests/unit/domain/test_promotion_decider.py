import pytest

from finetune.domain.entities import EvalResult
from finetune.domain.services.promotion_decider import PromotionDeciderService, PromotionPolicy


@pytest.fixture
def policy():
    return PromotionPolicy(
        min_accuracy_improvement=0.005,
        min_f1_improvement=0.003,
        max_per_class_regression=0.02,
        min_regression_pass_rate=1.0,
        min_test_set_size=10,  # small for testing
    )


@pytest.fixture
def decider(policy):
    return PromotionDeciderService(policy=policy)


@pytest.fixture
def baseline():
    return EvalResult(
        accuracy=0.80,
        f1_macro=0.78,
        f1_per_class={"happy": 0.85, "sad": 0.70},
        regression_pass_rate=1.0,
        benchmark_size=100,
    )


def test_promote_when_all_criteria_met(decider, baseline):
    candidate = EvalResult(
        accuracy=0.81,
        f1_macro=0.785,
        f1_per_class={"happy": 0.86, "sad": 0.71},
        regression_pass_rate=1.0,
        benchmark_size=100,
    )
    promote, reason = decider.decide(candidate, baseline)
    assert promote is True


def test_reject_low_accuracy(decider, baseline):
    candidate = EvalResult(
        accuracy=0.802,  # +0.2%, below +0.5% threshold
        f1_macro=0.785,
        f1_per_class={"happy": 0.86, "sad": 0.71},
        regression_pass_rate=1.0,
        benchmark_size=100,
    )
    promote, reason = decider.decide(candidate, baseline)
    assert promote is False
    assert "Accuracy" in reason


def test_reject_per_class_regression(decider, baseline):
    candidate = EvalResult(
        accuracy=0.81,
        f1_macro=0.785,
        f1_per_class={"happy": 0.86, "sad": 0.67},  # sad dropped 3% > 2%
        regression_pass_rate=1.0,
        benchmark_size=100,
    )
    promote, reason = decider.decide(candidate, baseline)
    assert promote is False
    assert "sad" in reason


def test_reject_regression_not_100pct(decider, baseline):
    candidate = EvalResult(
        accuracy=0.81,
        f1_macro=0.785,
        f1_per_class={"happy": 0.86, "sad": 0.71},
        regression_pass_rate=0.95,
        benchmark_size=100,
    )
    promote, reason = decider.decide(candidate, baseline)
    assert promote is False
    assert "Regression" in reason
