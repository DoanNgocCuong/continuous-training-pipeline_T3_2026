from dataclasses import dataclass
from enum import Enum


class EmotionLabel(str, Enum):
    HAPPY = "happy"
    ACHIEVEMENT = "achievement"
    THINKING = "thinking"
    CALM = "calm"
    SURPRISED = "surprised"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "EmotionLabel":
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.UNKNOWN


class AgreementStatus(str, Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    FLAGGED = "flagged"
    HUMAN_RESOLVED = "human_resolved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ConfidenceScore:
    value: float

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.value}")

    @property
    def is_high(self) -> bool:
        return self.value >= 0.8

    @property
    def is_low(self) -> bool:
        return self.value < 0.5
