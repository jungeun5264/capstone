from typing import List, Literal
from pydantic import BaseModel, Field

class ScoreItem(BaseModel):
    score: int = Field(ge=0, le=20, description="0~20점 사이의 평가 점수")
    reason: str = Field(description="이 점수를 준 구체적인 이유")
    improvement: str = Field(description="이 항목을 개선하는 구체적인 방법")

class Scores(BaseModel):
    goal: ScoreItem
    context: ScoreItem
    constraints: ScoreItem
    output: ScoreItem
    verification: ScoreItem

class PromptAnalysis(BaseModel):
    intent: str
    task_type: str
    scores: Scores
    strengths: List[str]
    improvements: List[str]
    coach_questions: List[str]
    revised_prompt: str
    learning_point: str
    capability_focus: Literal["Understand", "Use", "Select", "Evaluate", "Safety"]
    capability_reason: str
