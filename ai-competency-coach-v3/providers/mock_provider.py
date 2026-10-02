from dataset import question_index, competency_index
from schemas import EvaluationResult

class MockProvider:
    """Gemini 연결 전 UI/API 연결 확인용 가짜 Judge."""
    def evaluate(self, question_id: str, answer: str) -> EvaluationResult:
        qidx = question_index()
        cidx = competency_index()

        if question_id not in qidx:
            raise KeyError(f"Unknown question_id: {question_id}")

        q = qidx[question_id]
        comp = cidx[q["competency_id"]]
        evidence = {x["id"]: "partial" for x in comp["evidence"]}

        return EvaluationResult(
            question_id=question_id,
            competency_id=comp["id"],
            score=1,
            evidence=evidence,
            reason="Mock 모드입니다. 실제 AI 채점이 아니라 구조 테스트용 결과입니다.",
            feedback="API와 UI가 정해진 JSON 형식을 정상적으로 주고받는지 확인하세요.",
            next_step="실제 모델 연결 후 rubric 기반 평가를 실행하세요.",
            confidence=0.0
        )
