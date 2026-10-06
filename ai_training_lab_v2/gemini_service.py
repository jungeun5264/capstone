from __future__ import annotations
import json
import re
from typing import Any, Dict, List
from google import genai
from google.genai import types

from scoring import ABILITY_META, ABILITY_ORDER


def _mission_context(mission: Dict[str, Any], active_events: List[str]) -> str:
    events = "\n".join(f"- {e}" for e in active_events) if active_events else "- 아직 추가 상황 없음"
    return f"""
과제명: {mission['title']}
상황: {mission['situation']}
제약 조건: {', '.join(mission['constraints'])}
수행 목표: {', '.join(mission['goals'])}
현재까지 공개된 파생 상황:
{events}
""".strip()


def chat_reply(api_key: str, model: str, mission: Dict[str, Any], active_events: List[str], messages: List[Dict[str, str]]) -> str:
    client = genai.Client(api_key=api_key)
    transcript = []
    for m in messages:
        role = "사용자" if m["role"] == "user" else "AI"
        transcript.append(f"{role}: {m['content']}")
    prompt = "\n\n".join(transcript)
    system = f"""
당신은 사용자가 실전 과제를 해결할 때 활용하는 AI 어시스턴트입니다.

{_mission_context(mission, active_events)}

규칙:
1. 사용자의 AI 역량을 평가하거나 점수를 언급하지 마세요.
2. 사용자가 더 높은 평가를 받도록 정답 행동을 직접 가르치지 마세요.
3. 사용자가 제공하지 않은 사실을 확정적으로 지어내지 마세요.
4. 최신 가격·운영시간·수치·출처 등 확인할 수 없는 정보는 불확실성을 명시하세요.
5. 현재 공개된 파생 상황을 고려해 대답하세요.
6. 사용자의 기준과 요청을 존중하되, 최종 의사결정을 대신 확정하지 마세요.
7. 한국어로 자연스럽고 실용적으로 답하세요.
""".strip()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0.7),
    )
    return response.text or ""


def _schema_example() -> Dict[str, Any]:
    block_fields = {
        "ai_basic": ["limitations_awareness", "uncertainty_awareness", "appropriate_use"],
        "ai_usage": ["goal_definition", "context_constraints", "iterative_refinement"],
        "human_agency": ["criteria_setting", "critical_selection", "decision_ownership"],
        "human_responsibility": ["verification", "uncertainty_handling", "final_review"],
        "ethical_view": ["bias_fairness", "stakeholder_impact", "honest_use"],
        "safe_use": ["privacy", "confidentiality", "risk_management"],
    }
    out: Dict[str, Any] = {}
    for key, fields in block_fields.items():
        out[key] = {"evaluated": True, **{f: 0 for f in fields}, "evidence": [], "feedback": ""}
    out.update({
        "strength_feedback": "",
        "improvement_feedback": "",
        "next_action": "",
        "event_feedback": "",
        "deliverable_feedback": "",
    })
    return out


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)


def evaluate(api_key: str, model: str, mission: Dict[str, Any], active_events: List[str], messages: List[Dict[str, str]], final_output: Dict[str, str]) -> Dict[str, Any]:
    client = genai.Client(api_key=api_key)
    transcript = "\n\n".join(
        f"{'USER' if m['role']=='user' else 'AI'}: {m['content']}" for m in messages
    )
    output_text = "\n".join(f"{k}: {v}" for k, v in final_output.items())
    target_labels = [ABILITY_META[k]["label"] for k in mission.get("target_abilities", [])]
    example = json.dumps(_schema_example(), ensure_ascii=False)
    prompt = f"""
당신은 AI 활용 역량 평가자입니다. AI 답변의 품질이 아니라 사용자의 AI 활용 행동을 평가하세요.

[과제]
{_mission_context(mission, active_events)}
주요 관찰 역량: {', '.join(target_labels)}

[전체 대화]
{transcript}

[사용자가 작성한 최종 결과물]
{output_text}

[채점 기준]
각 세부 항목은 0~4점입니다.
0: 역량과 반대되는 행동 / 1: 매우 제한적 / 2: 일부 수행 / 3: 적절한 수행 / 4: 적극적이고 일관된 수행
관찰할 근거가 없고 과제 구조상 해당 역량을 평가하기 어렵다면 evaluated=false로 하세요.
'문제가 없었다'는 이유만으로 높은 점수를 주지 마세요.
프롬프트 길이 자체는 점수 기준이 아닙니다.
파생 상황에 어떻게 대응했는지, AI 결과를 수정·검증했는지, 최종 결과물에 사용자의 판단이 남아있는지를 중요하게 보세요.

[6개 역량 의미]
- AI의 기초 이해: AI의 한계·불확실성·적절한 활용 범위를 인식하는가
- AI 활용 능력: 목적·맥락·조건을 전달하고 후속 대화로 결과를 개선하는가
- 인간의 주도권: 판단 기준과 최종 결정을 사용자가 주도하는가
- 인간의 책임: 사실·수치·출처·불확실성을 확인하고 최종 검토하는가
- 윤리적 관점: 편향·공정성·정직성·이해관계자 영향을 고려하는가
- 안전하고 책임 있는 사용: 개인정보·기밀·민감정보·보안 위험을 관리하는가

반드시 JSON만 출력하세요. 키 구조는 아래 예시와 정확히 같아야 합니다.
{example}
각 능력의 세부 점수는 반드시 0~4 정수입니다. evidence는 사용자 행동 근거의 요약입니다.
""".strip()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
    )
    return _extract_json(response.text or "{}")
