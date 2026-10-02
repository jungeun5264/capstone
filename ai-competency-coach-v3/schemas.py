from typing import Dict, Literal
from pydantic import BaseModel, Field

EvidenceStatus = Literal["absent", "partial", "clear"]

class EvaluationResult(BaseModel):
    question_id: str
    competency_id: str
    score: int = Field(ge=0, le=3)
    evidence: Dict[str, EvidenceStatus]
    reason: str
    feedback: str
    next_step: str
    confidence: float = Field(ge=0.0, le=1.0)

class EvaluateRequest(BaseModel):
    question_id: str
    answer: str = Field(min_length=1)
