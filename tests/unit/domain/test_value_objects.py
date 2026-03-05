import pytest

from finetune.domain.value_objects import ConfidenceScore, EmotionLabel


def test_emotion_label_from_string_valid():
    assert EmotionLabel.from_string("happy") == EmotionLabel.HAPPY
    assert EmotionLabel.from_string("HAPPY") == EmotionLabel.HAPPY
    assert EmotionLabel.from_string("  happy  ") == EmotionLabel.HAPPY


def test_emotion_label_from_string_invalid():
    assert EmotionLabel.from_string("not_an_emotion") == EmotionLabel.UNKNOWN
    assert EmotionLabel.from_string("") == EmotionLabel.UNKNOWN


def test_confidence_score_valid():
    score = ConfidenceScore(0.9)
    assert score.is_high is True
    assert score.is_low is False


def test_confidence_score_low():
    score = ConfidenceScore(0.3)
    assert score.is_high is False
    assert score.is_low is True


def test_confidence_score_out_of_range():
    with pytest.raises(ValueError):
        ConfidenceScore(1.1)
    with pytest.raises(ValueError):
        ConfidenceScore(-0.1)
