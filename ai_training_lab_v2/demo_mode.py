from __future__ import annotations
from typing import Any, Dict, List


def demo_reply(user_text: str, mission: Dict[str, Any], events: List[str]) -> str:
    title = mission["title"]
    latest = events[-1] if events else ""
    if latest:
        return (
            f"좋아요. 현재 과제 **{title}**에서 새 조건인 ‘{latest}’를 반영해볼게요. "
            "기존 계획에서 유지할 부분과 바꿀 부분을 나누면 더 명확합니다. "
            "원하시면 선택지 2~3개와 각각의 장단점까지 비교해드릴게요."
        )
    return (
        f"좋아요. **{title}**를 함께 해결해볼게요. 우선 지금 주어진 조건을 기준으로 초안을 만들 수 있습니다. "
        "원하는 우선순위나 추가 조건이 있으면 알려주시면 그 기준에 맞춰 계속 수정하겠습니다."
    )


def _has(text: str, words: List[str]) -> bool:
    return any(w in text for w in words)


def demo_evaluate(messages: List[Dict[str, str]], final_output: Dict[str, str], active_events: List[str], mission: Dict[str, Any]) -> Dict[str, Any]:
    user = " ".join(m["content"] for m in messages if m.get("role") == "user").lower()
    out = " ".join(final_output.values()).lower()
    combined = user + " " + out
    turns = len([m for m in messages if m.get("role") == "user"])
    has_constraints = _has(combined, ["예산", "조건", "제약", "시간", "목표", "우선", "기준"])
    has_refine = _has(combined, ["수정", "다시", "바꿔", "조정", "제외", "대안", "비교"])
    has_verify = _has(combined, ["확인", "출처", "최신", "검증", "정확", "불확실", "확정", "예상"])
    has_decide = _has(combined, ["선택", "결정", "우선", "기준", "중요", "유지", "제외"])
    has_ethics = _has(combined, ["공정", "차별", "과장", "허위", "정직", "이해관계", "왜곡"])
    has_safe = _has(combined, ["개인정보", "기밀", "이름", "민감", "보안", "내부정보", "익명"])
    has_review = _has(combined, ["최종", "검토", "누락", "모순", "체크", "점검"])

    def block(evaluated, a, b, c, evidence, feedback):
        return {"evaluated": evaluated, **a, **b, **c, "evidence": evidence, "feedback": feedback}

    result: Dict[str, Any] = {
        "ai_basic": block(True,
            {"limitations_awareness": 4 if has_verify else 2},
            {"uncertainty_awareness": 4 if has_verify else 2},
            {"appropriate_use": 4 if turns >= 3 else 3 if turns >= 1 else 1},
            ["AI 답변의 한계·불확실성에 대한 확인 행동을 보았습니다."],
            "AI가 항상 확정적인 답을 주는 것은 아니라는 점을 행동으로 다뤘는지 평가했습니다."),
        "ai_usage": block(True,
            {"goal_definition": 4 if has_constraints else 3},
            {"context_constraints": 4 if has_constraints else 2},
            {"iterative_refinement": 4 if has_refine and turns >= 3 else 3 if has_refine else 2},
            [f"사용자 대화 {turns}회와 조건·후속 수정 행동을 확인했습니다."],
            "목표·조건 전달과 반복적인 개선 요청을 평가했습니다."),
        "human_agency": block(True,
            {"criteria_setting": 4 if has_decide else 2},
            {"critical_selection": 4 if has_refine else 2},
            {"decision_ownership": 4 if has_decide else 2},
            ["AI가 제안한 내용을 사용자가 자신의 기준으로 조정했는지 확인했습니다."],
            "최종 방향과 선택을 사용자가 주도했는지 평가했습니다."),
        "human_responsibility": block(True,
            {"verification": 4 if has_verify else 2},
            {"uncertainty_handling": 4 if has_verify else 2},
            {"final_review": 4 if has_review or len(out) > 120 else 3},
            ["검증 표현과 최종 결과물 작성 여부를 확인했습니다."],
            "AI 결과를 사용하기 전 확인하고 정리한 행동을 평가했습니다."),
        "ethical_view": block(has_ethics or "ethical_view" in mission.get("target_abilities", []),
            {"bias_fairness": 3 if has_ethics else 2},
            {"stakeholder_impact": 4 if has_ethics else 2},
            {"honest_use": 4 if has_ethics else 2},
            ["과장·정직성·타인 영향과 관련한 행동을 확인했습니다."] if has_ethics else [],
            "윤리적 판단이 필요한 장면에서 사용자의 선택을 평가했습니다."),
        "safe_use": block(has_safe or "safe_use" in mission.get("target_abilities", []),
            {"privacy": 4 if has_safe else 2},
            {"confidentiality": 4 if has_safe else 2},
            {"risk_management": 4 if has_safe else 2},
            ["개인정보·기밀·민감정보 처리 관련 행동을 확인했습니다."] if has_safe else [],
            "안전하고 책임 있는 정보 입력 및 활용 여부를 평가했습니다."),
        "strength_feedback": "주어진 조건을 AI와의 대화에 반영하고, 결과물을 직접 정리한 점이 좋았습니다.",
        "improvement_feedback": "AI가 제안한 정보 중 검증이 필요한 사실·수치와 사용자가 직접 결정해야 할 부분을 더 명확히 구분해보세요.",
        "next_action": "다음 도전에서는 AI 답변에서 확인이 필요한 정보 한 가지를 직접 표시하고, 최종 선택 이유를 한 문장으로 남겨보세요.",
        "event_feedback": f"총 {len(active_events)}개의 파생 상황 중 {min(len(active_events), turns)}개 이상에 대화로 대응했습니다.",
        "deliverable_feedback": "최종 결과물의 구체성과 사용자의 판단 근거를 함께 확인했습니다.",
    }
    return result
