import pytest

from finetune.domain.entities import EmotionSample
from finetune.domain.value_objects import AgreementStatus, EmotionLabel


@pytest.fixture
def sample_all_agree():
    return EmotionSample(
        input_text="Tớ rất vui!",
        ai_label=EmotionLabel.HAPPY,
        human_label=EmotionLabel.HAPPY,
        model_output=EmotionLabel.HAPPY,
    )


@pytest.fixture
def sample_ai_human_agree_model_disagree():
    return EmotionSample(
        input_text="Cậu giỏi quá!",
        ai_label=EmotionLabel.ACHIEVEMENT,
        human_label=EmotionLabel.ACHIEVEMENT,
        model_output=EmotionLabel.HAPPY,
    )


@pytest.fixture
def sample_ai_model_agree_human_disagree():
    return EmotionSample(
        input_text="Ồ không!",
        ai_label=EmotionLabel.WORRIED,
        human_label=EmotionLabel.SAD,
        model_output=EmotionLabel.WORRIED,
    )


@pytest.fixture
def sample_conflict():
    # Case 4: AI != Human (all 3 different) → FLAGGED
    return EmotionSample(
        input_text="Hmm...",
        ai_label=EmotionLabel.THINKING,
        human_label=EmotionLabel.CALM,
        model_output=EmotionLabel.HAPPY,
    )


@pytest.fixture
def sample_no_human_agree():
    return EmotionSample(
        input_text="Tuyệt vời!",
        ai_label=EmotionLabel.HAPPY,
        human_label=None,
        model_output=EmotionLabel.HAPPY,
    )


@pytest.fixture
def sample_no_human_disagree():
    return EmotionSample(
        input_text="...",
        ai_label=EmotionLabel.CALM,
        human_label=None,
        model_output=EmotionLabel.THINKING,
    )
