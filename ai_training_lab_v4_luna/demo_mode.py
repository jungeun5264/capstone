from __future__ import annotations
from typing import Any, Dict, List


def demo_plan(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "opening_message": "좋아요. 이 과제를 함께 해결해볼게요. 원하는 방식으로 저에게 요청을 시작해보세요.",
        "events": mission["fallback_events"],
    }


def demo_reply(user_text: str, mission: Dict[str, Any], events: List[Dict[str, str]]) -> str:
    if events:
        latest = events[-1]
        return f"새 조건인 ‘{latest['situation']}’까지 반영해서 생각해볼 수 있어요. 지금 정한 우선순위를 기준으로 기존 안에서 유지할 것과 바꿀 것을 나눠볼까요?"
    return f"좋아요. **{mission['title']}**에 맞춰 같이 정리해볼게요. 방금 말해준 기준을 바탕으로 초안을 만들거나 선택지를 비교할 수 있어요."


def demo_evaluate(messages, final_output, events, mission):
    user = " ".join(m["content"] for m in messages if m["role"] == "user")
    out = " ".join(final_output.values())
    text = user + " " + out
    turns = sum(1 for m in messages if m["role"] == "user")
    def has(*words): return any(w in text for w in words)
    def b(e, vals, ev, fb): return {"evaluated": e, **vals, "evidence": ev, "feedback": fb}
    return {
        "ai_basic": b(True, {"limitations_awareness": 4 if has("확인","검증","출처") else 2, "uncertainty_awareness": 4 if has("최신","변동","불확실","예상") else 2, "appropriate_use": 3}, ["정보의 한계와 확인 필요성을 다룬 행동을 확인했습니다."], "AI 정보의 확실성과 한계를 구분했는지 평가했습니다."),
        "ai_usage": b(True, {"goal_definition": 4 if has("목표","우선","기준") else 3, "context_constraints": 4 if has("예산","조건","시간") else 2, "iterative_refinement": 4 if turns >= 4 and has("수정","다시","바꿔","조정") else 3 if turns >= 2 else 2}, [f"총 {turns}회의 사용자 대화를 확인했습니다."], "조건 전달과 반복 개선 행동을 평가했습니다."),
        "human_agency": b(True, {"criteria_setting": 4 if has("우선","기준","중요") else 2, "critical_selection": 4 if has("제외","선택","비교","수정") else 2, "decision_ownership": 4 if has("선택","결정","유지") else 2}, ["사용자가 선택 기준을 직접 세웠는지 확인했습니다."], "AI가 아니라 사용자가 방향을 결정했는지 평가했습니다."),
        "human_responsibility": b(True, {"verification": 4 if has("확인","검증","출처") else 2, "uncertainty_handling": 4 if has("최신","변동","예상","불확실") else 2, "final_review": 4 if has("최종","점검","누락") or len(out) > 150 else 3}, ["최종 결과와 검증 관련 행동을 확인했습니다."], "최종 사용 전 확인 행동을 평가했습니다."),
        "ethical_view": b("ethical_view" in mission["target_abilities"], {"bias_fairness": 3, "stakeholder_impact": 3, "honest_use": 3}, [], "이번 과제에서 윤리적 고려가 나타났는지 평가했습니다."),
        "safe_use": b("safe_use" in mission["target_abilities"], {"privacy": 3, "confidentiality": 3, "risk_management": 3}, [], "민감 정보를 안전하게 다뤘는지 평가했습니다."),
        "strength_feedback": "AI에게 단순히 답을 맡기기보다 조건을 반영하며 결과를 발전시킨 점이 좋았습니다.",
        "improvement_feedback": "AI가 제시한 정보 중 실제 확인이 필요한 부분과 사용자가 직접 결정할 부분을 조금 더 명확히 나눠보세요.",
        "next_action": "다음에는 AI 답변에서 확인이 필요한 정보 한 가지와 내가 직접 결정한 기준 한 가지를 명시해보세요.",
        "event_feedback": f"공개된 {len(events)}개의 추가 상황을 기존 계획과 연결해 대응했습니다.",
        "deliverable_feedback": "대화와 별도로 최종 결과물을 직접 정리했는지 확인했습니다.",
    }
