import os
import json
import streamlit as st
from google import genai
from google.genai import types

# Secrets
for key in ("GEMINI_API_KEY", "GEMINI_MODEL"):
    try:
        if key in st.secrets and st.secrets[key]:
            os.environ[key] = str(st.secrets[key])
    except Exception:
        pass

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not API_KEY or not MODEL:
    st.error("Streamlit Secrets에 GEMINI_API_KEY와 GEMINI_MODEL을 설정해주세요.")
    st.stop()

client = genai.Client(api_key=API_KEY)

SOURCE_FRAMEWORK = [
    {
        "id": "HC_AGENCY",
        "name": "인간의 주도권",
        "criterion": "AI가 결정을 대신하는 도구가 아니라는 점을 이해하고, 어떤 일에 AI를 사용할지 사람이 목적과 범위를 정한다."
    },
    {
        "id": "HC_RESPONSIBILITY",
        "name": "인간의 책임",
        "criterion": "AI 답변을 그대로 채택하지 않고, 중요한 판단에서는 근거를 확인한 뒤 최종 선택과 책임을 사람이 맡는다."
    },
    {
        "id": "ETH_PERSPECTIVE",
        "name": "윤리적 관점",
        "criterion": "AI 사용이 타인의 권리, 편향, 포용성에 영향을 줄 수 있음을 이해하고 문제 상황을 알아본다."
    },
    {
        "id": "ETH_SAFE_USE",
        "name": "안전하고 책임 있는 사용",
        "criterion": "AI에 입력할 개인정보를 가려내고, 결과물을 사용하거나 공유할 때 개인정보·저작권 문제를 확인한다."
    },
    {
        "id": "TECH_FOUNDATION",
        "name": "AI의 기초",
        "criterion": "AI가 할 수 있는 일과 한계를 구별하고, 그럴듯한 답변에도 오류가 있을 수 있음을 이해한다."
    },
    {
        "id": "TECH_USE",
        "name": "활용 능력",
        "criterion": "목적에 맞는 AI 도구를 고르고, 필요한 맥락·조건을 담아 질문하며, 결과를 보고 질문이나 활용 방식을 조정한다."
    }
]

RUBRIC = {
    "HC_AGENCY": {
        "0": "AI에게 목적과 판단을 거의 전적으로 위임",
        "1": "인간 판단 필요성은 인식하지만 역할 구분이 약함",
        "2": "AI와 인간의 역할은 대체로 구분하나 목적/기준 설정이 부족",
        "3": "사람이 목적/기준을 정하고 AI 역할을 한정하며 최종 판단도 직접 함"
    },
    "HC_RESPONSIBILITY": {
        "0": "AI 결과를 검증 없이 채택",
        "1": "확인 필요성만 막연히 인식",
        "2": "구체적으로 검증하지만 최종 책임 인식이 약함",
        "3": "검증, 근거 확인, 인간의 최종 책임이 모두 명확"
    },
    "ETH_PERSPECTIVE": {
        "0": "윤리적 문제를 거의 인식하지 못함",
        "1": "공정성/권리 문제 가능성만 막연히 언급",
        "2": "편향·차별·권리 문제를 구체적으로 인식",
        "3": "권리, 편향, 포용성과 영향 집단까지 다각도로 설명"
    },
    "ETH_SAFE_USE": {
        "0": "개인정보·기밀·저작권 위험을 인식하지 못함",
        "1": "조심해야 한다는 인식만 있음",
        "2": "비식별화·최소입력·권한확인 등 적절한 보호 행동 제시",
        "3": "위험 식별, 보호 행동, 정책/권리 확인을 종합적으로 수행"
    },
    "TECH_FOUNDATION": {
        "0": "AI 답변을 사실상 정답으로 봄",
        "1": "AI가 가끔 틀릴 수 있다는 정도만 인식",
        "2": "오류 가능성과 주요 한계를 이해",
        "3": "작업·도구 특성에 따라 강점과 한계, 정보 접근 범위를 구분"
    },
    "TECH_USE": {
        "0": "도구 선택/맥락 없이 모호하게 요청하고 첫 결과를 그대로 사용",
        "1": "기본 요청은 가능하지만 맥락/조건/후속 개선이 부족",
        "2": "주요 맥락과 조건을 제공하고 결과에 따라 추가 요청 가능",
        "3": "도구 선택, 입력 설계, 결과 검토와 반복 개선이 모두 명확"
    }
}

SYSTEM = """
너는 AI 활용 역량을 진단하는 대화형 Coach & Judge다.

최상위 평가기준은 source_framework의 6개 criterion이다.
rubric은 각 criterion을 실제 대화에서 관찰하기 위한 보조 기준이다.

규칙:
- 현재까지의 대화에서 실제 근거가 있는 역량만 평가한다.
- 근거가 없는 역량은 0점이 아니라 '판단 보류'다.
- 특정 단어, 문장 길이, 말투만으로 점수를 주지 않는다.
- 사용자가 말하지 않은 행동을 추정하지 않는다.
- 점수는 0~3이다.
- 사용자가 새 정보를 주면 이전 판단을 업데이트할 수 있다.
- 후속 질문은 최대 2개만 만든다.
- 반드시 JSON만 반환한다.
- 한국어로 답한다.
"""

def build_prompt(user_messages):
    return SYSTEM + "\n\n" + json.dumps({
        "source_framework": SOURCE_FRAMEWORK,
        "rubric": RUBRIC,
        "conversation": user_messages,
        "return_json": {
            "summary": "사용자의 AI 활용 방식 요약",
            "scored_competencies": [
                {
                    "competency_id": "역량 ID",
                    "competency_name": "역량명",
                    "score": "0~3",
                    "reason": "대화에서 관찰된 근거",
                    "strength": "잘한 점",
                    "improvement": "보완할 점"
                }
            ],
            "unobserved_competencies": [
                {
                    "competency_id": "역량 ID",
                    "competency_name": "역량명",
                    "reason": "왜 아직 판단하기 어려운지"
                }
            ],
            "overall_coaching": "전체 코칭",
            "follow_up_questions": ["필요한 경우 최대 2개"]
        }
    }, ensure_ascii=False, indent=2)

def analyze(user_messages):
    response = client.models.generate_content(
        model=MODEL,
        contents=build_prompt(user_messages),
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )
    if not response.text:
        raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
    return json.loads(response.text)

st.set_page_config(page_title="AI Competency Chat Test", page_icon="🧠")
st.title("🧠 AI Competency Chat Test")
st.caption("UI 디자인 전, 기능만 확인하는 채팅형 테스트")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(
            "AI를 어떻게 쓰려고 하는지 편하게 말해주세요. "
            "실제 프롬프트를 붙여넣어도 되고, 사용 상황을 설명해도 됩니다."
        )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("analysis"):
            a = m["analysis"]
            scored = a.get("scored_competencies", [])
            if scored:
                st.markdown("**관찰된 역량**")
                for item in scored:
                    st.write(
                        f"- **{item.get('competency_name')} {item.get('score')}/3**: "
                        f"{item.get('reason')}"
                    )
            followups = a.get("follow_up_questions", [])
            if followups:
                st.markdown("**추가로 물어볼 점**")
                for q in followups[:2]:
                    st.write(f"- {q}")

user_text = st.chat_input("메시지를 입력하세요")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.chat_message("user"):
        st.write(user_text)

    user_history = [
        {"role": "user", "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] == "user"
    ]

    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            try:
                result = analyze(user_history)
                text = result.get("overall_coaching", "분석했습니다.")
                st.write(text)

                scored = result.get("scored_competencies", [])
                if scored:
                    st.markdown("**관찰된 역량**")
                    for item in scored:
                        st.write(
                            f"- **{item.get('competency_name')} {item.get('score')}/3**: "
                            f"{item.get('reason')}"
                        )
                        if item.get("strength"):
                            st.caption(f"강점: {item['strength']}")
                        if item.get("improvement"):
                            st.caption(f"보완: {item['improvement']}")

                unobserved = result.get("unobserved_competencies", [])
                if unobserved:
                    with st.expander("아직 판단하기 어려운 역량"):
                        for item in unobserved:
                            st.write(f"- {item.get('competency_name')}: {item.get('reason')}")

                followups = result.get("follow_up_questions", [])
                if followups:
                    st.markdown("**추가로 물어볼 점**")
                    for q in followups[:2]:
                        st.write(f"- {q}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": text,
                    "analysis": result
                })

            except Exception as e:
                st.error("Gemini 분석 중 오류가 발생했습니다.")
                with st.expander("오류 상세"):
                    st.code(f"{type(e).__name__}: {e}")

st.divider()
if st.button("대화 초기화"):
    st.session_state.messages = []
    st.rerun()
