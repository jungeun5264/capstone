from __future__ import annotations

import json
from typing import Any, Dict, List

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from scoring import ABILITY_META


class BranchEvent(BaseModel):
    title: str = Field(description="사용자에게 보여줄 짧은 상황 제목")
    situation: str = Field(description="기존 과제를 흔드는 새로운 조건 또는 정보")
    task: str = Field(description="사용자가 AI와 해결해야 할 과제. 평가 행동을 직접 힌트로 주면 안 됨")


class TrainingPlan(BaseModel):
    opening_message: str = Field(description="과제를 시작하는 자연스러운 AI 첫 인사. 해결법을 가르치지 않음")
    events: List[BranchEvent] = Field(min_length=3, max_length=3)


def _client(api_key: str):
    return genai.Client(api_key=api_key)


def _mission_text(mission: Dict[str, Any]) -> str:
    return (
        f"과제명: {mission['title']}\n"
        f"상황: {mission['situation']}\n"
        f"목표: {' / '.join(mission['goals'])}\n"
        f"제약: {' / '.join(mission['constraints'])}"
    )


def create_training_plan(api_key: str, model: str, mission: Dict[str, Any], attempt_no: int) -> Dict[str, Any]:
    prompt = f"""
다음 AI 활용 훈련 과제를 위한 3개의 연속 파생 상황을 설계하세요.

{_mission_text(mission)}
재도전 번호: {attempt_no}

설계 원칙:
- 세 상황은 서로 다른 종류의 판단을 요구해야 합니다.
- 1번째는 요구사항/제약 변화, 2번째는 우선순위 충돌 또는 자원 변화, 3번째는 정보의 신뢰성·불확실성·윤리·안전 중 과제와 자연스럽게 맞는 요소를 포함하세요.
- 사용자가 무엇을 해야 ‘높은 점수’를 받는지 직접 가르치지 마세요.
- 정답 하나가 아니라 AI와 대화하며 판단할 여지가 있게 만드세요.
- 현실적이고 짧게 작성하세요.
- opening_message는 친절하지만 과제 해결법을 선제적으로 제시하지 마세요.
""".strip()
    response = _client(api_key).models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TrainingPlan,
        ),
    )
    return json.loads(response.text)


def chat_reply(
    api_key: str,
    model: str,
    mission: Dict[str, Any],
    revealed_events: List[Dict[str, str]],
    messages: List[Dict[str, str]],
) -> str:
    transcript = "\n\n".join(
        f"{'사용자' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in messages[-12:]
    )
    event_text = "\n".join(
        f"- {e['title']}: {e['situation']} / 현재 과제: {e['task']}" for e in revealed_events
    ) or "- 아직 공개된 추가 상황 없음"
    system = f"""
당신은 ‘정답을 알려주는 튜터’가 아니라 사용자가 실전 문제를 해결할 때 사용하는 일반 목적 AI 어시스턴트입니다.

{_mission_text(mission)}
현재까지 공개된 파생 상황:
{event_text}

규칙:
1. 사용자의 AI 활용 능력을 평가하거나 점수를 말하지 마세요.
2. 높은 점수를 받는 법, 채점 기준, 모범 행동을 선제적으로 가르치지 마세요.
3. 사용자가 세운 기준과 결정을 존중하고, 필요한 분석·비교·초안 작성을 도우세요.
4. 사용자가 제공하지 않은 사실을 확정적으로 만들지 마세요.
5. 가격·통계·운영시간·최신 사실 등 확인되지 않은 정보는 확실한 사실처럼 말하지 마세요.
6. 최종 결정은 사용자 대신 단정하지 말고 선택 근거와 트레이드오프를 명확하게 제시하세요.
7. 답변은 과도하게 길지 않게, 실제 협업 대화처럼 자연스러운 한국어로 작성하세요.
""".strip()
    response = _client(api_key).models.generate_content(
        model=model,
        contents=transcript,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return response.text or ""


def evaluate(
    api_key: str,
    model: str,
    mission: Dict[str, Any],
    revealed_events: List[Dict[str, str]],
    messages: List[Dict[str, str]],
    final_output: Dict[str, str],
) -> Dict[str, Any]:
    transcript = "\n\n".join(
        f"{'USER' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in messages
    )
    output = "\n".join(f"{k}: {v}" for k, v in final_output.items())
    events = "\n".join(f"{i+1}. {e['title']} — {e['situation']} — {e['task']}" for i, e in enumerate(revealed_events))
    target = ", ".join(ABILITY_META[k]["label"] for k in mission.get("target_abilities", []))

    template = {
        "ai_basic": {"evaluated": True, "limitations_awareness": 0, "uncertainty_awareness": 0, "appropriate_use": 0, "evidence": [], "feedback": ""},
        "ai_usage": {"evaluated": True, "goal_definition": 0, "context_constraints": 0, "iterative_refinement": 0, "evidence": [], "feedback": ""},
        "human_agency": {"evaluated": True, "criteria_setting": 0, "critical_selection": 0, "decision_ownership": 0, "evidence": [], "feedback": ""},
        "human_responsibility": {"evaluated": True, "verification": 0, "uncertainty_handling": 0, "final_review": 0, "evidence": [], "feedback": ""},
        "ethical_view": {"evaluated": False, "bias_fairness": 0, "stakeholder_impact": 0, "honest_use": 0, "evidence": [], "feedback": ""},
        "safe_use": {"evaluated": False, "privacy": 0, "confidentiality": 0, "risk_management": 0, "evidence": [], "feedback": ""},
        "strength_feedback": "",
        "improvement_feedback": "",
        "next_action": "",
        "event_feedback": "",
        "deliverable_feedback": "",
    }

    prompt = f"""
당신은 AI 활용 역량 평가자입니다. AI 답변 자체의 품질이 아니라 사용자의 행동을 평가하세요.

[과제]
{_mission_text(mission)}
주요 관찰 역량: {target}

[공개된 파생 상황]
{events or '없음'}

[전체 대화]
{transcript}

[사용자가 직접 작성한 최종 결과물]
{output}

[평가 원칙]
- 세부 항목은 0~4 정수로 평가합니다: 0 역량과 반대되는 행동, 1 매우 제한적, 2 일부, 3 적절, 4 적극적이고 일관됨.
- 프롬프트 길이 자체는 점수 기준이 아닙니다.
- ‘검증해줘’ 같은 표현을 한 번 말한 것보다 실제로 의심·비교·수정·판단한 행동을 더 높게 평가하세요.
- AI가 잘 답한 것은 사용자 점수가 아닙니다.
- 관찰할 기회 자체가 없었던 역량은 evaluated=false로 두세요. ‘문제가 없었다’는 이유로 높은 점수를 주면 안 됩니다.
- 파생 상황에서 사용자가 무엇을 우선시했고 AI 결과를 어떻게 수정했는지, 최종 판단을 누가 했는지 중요하게 보세요.
- evidence에는 실제 대화나 결과물에서 관찰된 사용자의 행동을 짧게 요약하세요.

[6개 역량]
AI의 기초 이해: AI의 한계·불확실성·적절한 활용 범위를 인식하는가
AI 활용 능력: 목적·맥락·조건을 전달하고 후속 대화로 결과를 개선하는가
인간의 주도권: 판단 기준과 최종 결정을 사용자가 주도하는가
인간의 책임: 사실·수치·출처·불확실성을 확인하고 최종 검토하는가
윤리적 관점: 편향·공정성·정직성·이해관계자 영향을 고려하는가
안전하고 책임 있는 사용: 개인정보·기밀·민감정보·보안 위험을 관리하는가

아래 키 구조를 정확히 유지한 JSON만 출력하세요.
{json.dumps(template, ensure_ascii=False)}
""".strip()
    response = _client(api_key).models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)
