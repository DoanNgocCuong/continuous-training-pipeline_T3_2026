import pytest

from finetune.domain.services.label_agreement import LabelAgreementService
from finetune.domain.value_objects import AgreementStatus, EmotionLabel


@pytest.fixture
def service():
    return LabelAgreementService()


def test_case1_all_agree(service, sample_all_agree):
    result = service.resolve(sample_all_agree)
    assert result.agreement_status == AgreementStatus.AUTO_APPROVED
    assert result.agreed_label == EmotionLabel.HAPPY


def test_case2_ai_human_agree_model_disagree(service, sample_ai_human_agree_model_disagree):
    result = service.resolve(sample_ai_human_agree_model_disagree)
    assert result.agreement_status == AgreementStatus.AUTO_APPROVED
    assert result.agreed_label == EmotionLabel.ACHIEVEMENT


def test_case3_ai_model_agree_human_disagree(service, sample_ai_model_agree_human_disagree):
    result = service.resolve(sample_ai_model_agree_human_disagree)
    assert result.agreement_status == AgreementStatus.HUMAN_RESOLVED
    assert result.agreed_label == EmotionLabel.SAD  # trust human


def test_case4_conflict(service, sample_conflict):
    result = service.resolve(sample_conflict)
    assert result.agreement_status == AgreementStatus.FLAGGED
    assert result.agreed_label is None


def test_case5_no_human_agree(service, sample_no_human_agree):
    result = service.resolve(sample_no_human_agree)
    assert result.agreement_status == AgreementStatus.AUTO_APPROVED
    assert result.agreed_label == EmotionLabel.HAPPY


def test_case5_no_human_disagree(service, sample_no_human_disagree):
    result = service.resolve(sample_no_human_disagree)
    assert result.agreement_status == AgreementStatus.PENDING
    assert result.agreed_label is None


def test_batch_resolve_splits_approved_flagged(service, sample_all_agree, sample_conflict):
    approved, flagged = service.batch_resolve([sample_all_agree, sample_conflict])
    assert len(approved) == 1
    assert len(flagged) == 1
