import json
from typing import Any, Dict, List, Optional, Tuple

from google import genai


CHAT_SYSTEM_PROMPT = """
당신은 사용자가 주어진 미션을 해결할 때 활용할 수 있는 AI 어시스턴트입니다.

규칙:
1. 사용자의 AI 활용 능력을 평가하거나 점수를 언급하지 마세요.
2. 사용자가 더 좋은 질문을 하도록 교육하거나 정답 행동을 유도하지 마세요.
3. 사용자가 제공하지 않은 조건을 임의로 확정하지 마세요. 필요한 경우 가정임을 명확히 표시하세요.
4. 가격, 운영시간, 교통편 등 변동 가능한 정보는 확정적인 사실처럼 만들지 마세요.
5. 확인할 수 없는 최신 정보나 출처를 허위로 생성하지 마세요.
6. 사용자가 추가 요청을 하면 이전 대화 내용을 고려해 결과를 수정하세요.
7. 사용자가 미션을 수행하는 과정에 자연스럽게 협력하세요.
8. 답변은 한국어로 작성하세요.
""".strip()


EVALUATOR_SYSTEM_PROMPT = """
당신은 AI 활용 역량 평가자입니다.
사용자와 AI 사이의 전체 대화 기록을 분석하여 'AI가 얼마나 좋은 답변을 했는지'가 아니라
'사용자가 AI를 어떻게 사용했는지'를 평가합니다.

공통 채점 기준(각 세부 항목 0~4점):
0 = 역량과 반대되는 행동을 함
1 = 매우 제한적으로 나타남
2 = 일부 나타나지만 충분하지 않음
3 = 적절하게 수행함
4 = 적극적이고 일관되게 수행함

중요 원칙:
- 프롬프트 길이는 평가 기준이 아닙니다.
- 평가 기준을 말로 언급한 것만으로 점수를 주지 말고 실제 행동을 보세요.
- 관찰할 수 없는 행동은 추측하지 마세요.
- 이번 미션에서 역량을 판단할 근거가 부족하면 evaluated=false로 처리하세요.
- 같은 의미의 행동을 반복했다고 무조건 점수를 높이지 마세요.
- AI 결과를 그대로 수용한 것과 검토 후 의도적으로 수용한 것을 구분하세요.
- evidence에는 실제 사용자 발화/행동의 요지를 간결하게 기록하세요.
- 한국어로 평가하세요.

이번 여행 미션에서 기본적으로 적극 평가할 영역:
1) AI의 기초 이해
2) AI 활용 능력
3) 인간의 주도권
4) 인간의 책임

이번 여행 미션에서는 윤리적 관점, 안전하고 책임 있는 사용은 관련 행동이 명확히 나타난 경우에만 평가하고,
그렇지 않으면 evaluated=false로 처리하세요. '문제가 없었다'는 이유만으로 100점을 주지 마세요.
""".strip()


EVALUATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "ai_basic": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "limitations_awareness": {"type": "integer", "minimum": 0, "maximum": 4},
                "uncertainty_awareness": {"type": "integer", "minimum": 0, "maximum": 4},
                "appropriate_use": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "limitations_awareness", "uncertainty_awareness", "appropriate_use", "evidence", "feedback"],
        },
        "ai_usage": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "goal_definition": {"type": "integer", "minimum": 0, "maximum": 4},
                "context_constraints": {"type": "integer", "minimum": 0, "maximum": 4},
                "iterative_refinement": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "goal_definition", "context_constraints", "iterative_refinement", "evidence", "feedback"],
        },
        "human_agency": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "criteria_setting": {"type": "integer", "minimum": 0, "maximum": 4},
                "critical_selection": {"type": "integer", "minimum": 0, "maximum": 4},
                "decision_ownership": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "criteria_setting", "critical_selection", "decision_ownership", "evidence", "feedback"],
        },
        "human_responsibility": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "verification": {"type": "integer", "minimum": 0, "maximum": 4},
                "uncertainty_handling": {"type": "integer", "minimum": 0, "maximum": 4},
                "final_review": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "verification", "uncertainty_handling", "final_review", "evidence", "feedback"],
        },
        "ethical_view": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "bias_fairness": {"type": "integer", "minimum": 0, "maximum": 4},
                "stakeholder_impact": {"type": "integer", "minimum": 0, "maximum": 4},
                "honest_use": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "bias_fairness", "stakeholder_impact", "honest_use", "evidence", "feedback"],
        },
        "safe_use": {
            "type": "object",
            "properties": {
                "evaluated": {"type": "boolean"},
                "privacy": {"type": "integer", "minimum": 0, "maximum": 4},
                "confidentiality": {"type": "integer", "minimum": 0, "maximum": 4},
                "risk_management": {"type": "integer", "minimum": 0, "maximum": 4},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "feedback": {"type": "string"},
            },
            "required": ["evaluated", "privacy", "confidentiality", "risk_management", "evidence", "feedback"],
        },
        "strength_feedback": {"type": "string"},
        "improvement_feedback": {"type": "string"},
        "next_action": {"type": "string"},
    },
    "required": [
        "ai_basic", "ai_usage", "human_agency", "human_responsibility",
        "ethical_view", "safe_use", "strength_feedback", "improvement_feedback", "next_action"
    ],
}


MISSION_TEXT = """
미션: 친구들과 부산 2박 3일 여행 계획하기
상황:
- 대학생 친구 4명
- 11월 금요일~일요일, 2박 3일
- 서울 출발
- 자동차 없음
- 1인당 최대 예산 30만 원
- 맛집과 관광을 모두 즐기고 싶음
- 일요일 저녁 서울 복귀 필요
목표: AI를 활용하여 친구들에게 실제로 공유할 수 있는 여행 계획을 완성하기
""".strip()


def make_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def chat_once(
    api_key: str,
    model: str,
    user_text: str,
    previous_interaction_id: Optional[str] = None,
) -> Tuple[str, str]:
    client = make_client(api_key)
    kwargs: Dict[str, Any] = {
        "model": model,
        "input": user_text,
        "system_instruction": CHAT_SYSTEM_PROMPT,
        "generation_config": {"temperature": 0.7},
    }
    if previous_interaction_id:
        kwargs["previous_interaction_id"] = previous_interaction_id

    interaction = client.interactions.create(**kwargs)
    return interaction.output_text or "", interaction.id


def _format_transcript(messages: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    user_idx = 0
    assistant_idx = 0
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            user_idx += 1
            lines.append(f"USER-{user_idx}:\n{content}")
        elif role == "assistant":
            assistant_idx += 1
            lines.append(f"AI-{assistant_idx}:\n{content}")
    return "\n\n".join(lines)


def evaluate_conversation(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
) -> Dict[str, Any]:
    transcript = _format_transcript(messages)
    prompt = f"""
{MISSION_TEXT}

아래는 사용자가 미션을 수행하면서 AI와 나눈 전체 대화입니다.
사용자의 행동만을 중심으로 평가하세요.

=== 대화 기록 ===
{transcript}
=== 대화 기록 끝 ===

각 세부 항목을 0~4점으로 평가하고, 반드시 제공된 JSON schema에 맞춰 응답하세요.
""".strip()

    client = make_client(api_key)
    interaction = client.interactions.create(
        model=model,
        input=prompt,
        system_instruction=EVALUATOR_SYSTEM_PROMPT,
        generation_config={"temperature": 0.0},
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": EVALUATION_SCHEMA,
        },
    )
    return json.loads(interaction.output_text)
