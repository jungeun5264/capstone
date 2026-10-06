from __future__ import annotations

from typing import Any, Dict, List


def demo_assistant_reply(user_text: str, turn: int) -> str:
    text = user_text.lower()
    if turn == 1:
        return (
            "좋아요. 우선 2박 3일 부산 일정의 큰 틀을 잡아볼게요.\n\n"
            "**1일차** 서울 출발 → 부산 도착 → 해운대/광안리 중심 관광\n"
            "**2일차** 감천문화마을·남포동·자갈치시장 등 원도심 중심\n"
            "**3일차** 여유 있는 브런치와 마지막 관광 후 서울 복귀\n\n"
            "예산은 교통·숙박·식사·관광비를 나눠 계산할 수 있습니다. "
            "정확한 날짜와 숙소 형태에 따라 실제 비용은 달라질 수 있어요."
        )
    if any(k in text for k in ["수정", "다시", "너무", "이동", "묶", "조정"]):
        return (
            "동선을 줄이는 방향으로 수정해볼게요. 첫날은 해운대권, 둘째 날은 남포동권처럼 "
            "권역별로 묶으면 이동 부담을 줄일 수 있습니다. 원하시면 시간대별 일정과 예상 비용까지 정리할게요."
        )
    if any(k in text for k in ["가격", "비용", "예산", "30만", "확인", "출처", "최신"]):
        return (
            "예산표 형태로 정리하면 교통비·숙박비·식비·관광비를 구분하기 좋습니다. "
            "다만 실제 KTX·숙박 가격은 날짜와 예약 시점에 따라 달라질 수 있으니 최종 예약 전에 확인이 필요합니다."
        )
    return (
        "요청한 조건을 반영해서 계획을 더 구체화할 수 있어요. "
        "원하는 지역, 음식 비중, 이동 강도, 예산 배분 중 조정하고 싶은 부분을 말씀해 주세요."
    )


def _has_any(text: str, words: List[str]) -> bool:
    return any(w in text for w in words)


def _score(condition: bool, strong_condition: bool = False, base: int = 1) -> int:
    if strong_condition:
        return 4
    if condition:
        return 3
    return base


def demo_evaluate(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
    joined = " ".join(user_msgs).lower()
    turns = len(user_msgs)

    mentions_goal = _has_any(joined, ["부산", "여행", "일정", "계획"])
    mentions_constraints = _has_any(joined, ["30만", "예산", "4명", "대중교통", "자동차", "2박", "3일", "서울"])
    many_constraints = sum(w in joined for w in ["30만", "4명", "대중교통", "2박", "서울"]) >= 3
    refinement = turns >= 2 and _has_any(joined, ["수정", "다시", "너무", "조정", "바꿔", "제외", "묶"])
    verification = _has_any(joined, ["확인", "출처", "최신", "실제", "정확", "검증"])
    uncertainty = _has_any(joined, ["변동", "불확실", "예상", "확정", "달라질", "확인 필요"])
    criteria = _has_any(joined, ["우리는", "선호", "중요", "맛집", "관광", "여유", "이동", "비중"])
    critical = _has_any(joined, ["너무", "문제", "아닌", "수정", "다시", "조정", "비효율"])
    review = _has_any(joined, ["최종", "검토", "누락", "모순", "전체", "다시 확인"])

    usage_goal = 4 if mentions_goal and mentions_constraints else (3 if mentions_goal else 1)
    usage_context = 4 if many_constraints else (3 if mentions_constraints else 1)
    usage_iter = 4 if refinement and turns >= 3 else (3 if refinement else (2 if turns >= 2 else 1))

    result: Dict[str, Any] = {
        "ai_basic": {
            "evaluated": True,
            "limitations_awareness": 4 if verification and uncertainty else (3 if verification else 1),
            "uncertainty_awareness": 4 if uncertainty else (3 if verification else 1),
            "appropriate_use": 3 if turns >= 2 else 2,
            "evidence": ["가격·최신성·확인 필요성 관련 발화가 있었는지 확인했습니다."],
            "feedback": "AI 정보의 불확실성을 행동으로 인식했는지를 중심으로 평가했습니다.",
        },
        "ai_usage": {
            "evaluated": True,
            "goal_definition": usage_goal,
            "context_constraints": usage_context,
            "iterative_refinement": usage_iter,
            "evidence": [f"사용자 발화 {turns}회, 조건 제시와 후속 수정 요청 여부를 확인했습니다."],
            "feedback": "목적·조건 전달과 결과 개선 행동을 평가했습니다.",
        },
        "human_agency": {
            "evaluated": True,
            "criteria_setting": 4 if criteria and many_constraints else (3 if criteria else 1),
            "critical_selection": 4 if critical and turns >= 3 else (3 if critical else 1),
            "decision_ownership": 4 if criteria and refinement else (3 if criteria else 2),
            "evidence": ["사용자가 자신의 기준을 제시하고 AI 결과를 수정했는지 확인했습니다."],
            "feedback": "결정 방향을 사용자가 주도했는지를 평가했습니다.",
        },
        "human_responsibility": {
            "evaluated": True,
            "verification": 4 if verification and turns >= 3 else (3 if verification else 1),
            "uncertainty_handling": 4 if uncertainty else (3 if verification else 1),
            "final_review": 4 if review and turns >= 3 else (3 if review else 1),
            "evidence": ["사실·가격 확인과 최종 검토 요청 여부를 확인했습니다."],
            "feedback": "AI 결과를 사용하기 전 확인·검토한 행동을 평가했습니다.",
        },
        "ethical_view": {
            "evaluated": False,
            "bias_fairness": 0,
            "stakeholder_impact": 0,
            "honest_use": 0,
            "evidence": [],
            "feedback": "이번 여행 미션에서는 윤리적 판단을 충분히 관찰하기 어렵습니다.",
        },
        "safe_use": {
            "evaluated": False,
            "privacy": 0,
            "confidentiality": 0,
            "risk_management": 0,
            "evidence": [],
            "feedback": "이번 여행 미션에서는 안전·보안 판단을 충분히 관찰하기 어렵습니다.",
        },
        "strength_feedback": "조건을 구체적으로 전달하고 AI 답변을 수정하는 행동이 나타날수록 높은 평가를 받습니다.",
        "improvement_feedback": "AI가 제시한 가격·시간·사실 정보를 검증하고 최종 결과를 다시 검토하는 행동을 추가해보세요.",
        "next_action": "다음 도전에서는 AI가 제시한 구체적인 사실이나 수치 중 최소 한 가지를 직접 확인 대상으로 표시해보세요.",
    }
    return result
