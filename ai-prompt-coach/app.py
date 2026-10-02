import os
import streamlit as st
from prompt_coach import DEFAULT_MODEL, PromptCoach, to_api_payload

st.set_page_config(page_title="AI Prompt Coach", page_icon="🧠", layout="wide")

def read_secret(name: str, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

API_KEY = read_secret("GEMINI_API_KEY")
MODEL = read_secret("GEMINI_MODEL", DEFAULT_MODEL)

@st.cache_resource
def get_coach(api_key: str, model: str):
    return PromptCoach(api_key=api_key, model=model)

def render_score(label: str, item: dict):
    st.metric(label, f"{item['score']}/20")
    st.progress(item["score"] / 20)

st.title("🧠 AI Prompt Coach")
st.caption("AI를 대신 써주는 AI가 아니라, AI를 더 잘 쓰게 가르쳐주는 AI")
st.info(
    "현재 화면은 AI 기능을 검증하기 위한 프로토타입 UI입니다. "
    "결과는 구조화된 JSON으로도 제공되어 나중에 별도 웹 UI와 연결할 수 있습니다."
)

if not API_KEY:
    st.error("Gemini API Key가 설정되지 않았습니다. Streamlit Cloud Secrets에 GEMINI_API_KEY를 추가해주세요.")
    st.stop()

with st.sidebar:
    st.header("⚙️ 테스트 설정")
    target_ai = st.selectbox(
        "이 프롬프트를 사용할 AI",
        ["범용 AI", "ChatGPT", "Gemini", "Claude", "Microsoft Copilot", "코딩 AI", "이미지 생성 AI"],
    )
    st.caption(f"Gemini 분석 모델: `{MODEL}`")
    st.divider()
    st.caption("최종 UI에서는 api.py의 /analyze 결과를 친구가 만든 화면에 표시하면 됩니다.")

user_prompt = st.text_area("✏️ 평가할 프롬프트", placeholder="예: 논문 요약해줘", height=180)

if st.button("🔍 프롬프트 진단하기", type="primary", use_container_width=True):
    if not user_prompt.strip():
        st.warning("분석할 프롬프트를 입력해주세요.")
    else:
        try:
            with st.spinner("Gemini가 프롬프트를 분석하고 있습니다..."):
                result = get_coach(API_KEY, MODEL).analyze(user_prompt, target_ai)
                st.session_state["analysis"] = to_api_payload(result)
        except Exception as e:
            st.error("분석 중 오류가 발생했습니다.")
            st.exception(e)

if "analysis" in st.session_state:
    data = st.session_state["analysis"]
    scores = data["scores"]

    st.divider()
    st.subheader(f"Prompt Score · {data['total_score']}/100")

    cols = st.columns(5)
    labels = [
        ("🎯 Goal", "goal"),
        ("🧩 Context", "context"),
        ("📏 Constraints", "constraints"),
        ("📄 Output", "output"),
        ("🔎 Verification", "verification"),
    ]
    for col, (label, key) in zip(cols, labels):
        with col:
            render_score(label, scores[key])

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 종합 진단", "✨ 개선된 프롬프트", "🔎 세부 평가", "🧩 개발용 JSON"]
    )

    with tab1:
        st.markdown("### Gemini가 이해한 목적")
        st.write(data["intent"])
        st.caption(f"작업 유형: {data['task_type']}")

        left, right = st.columns(2)
        with left:
            st.markdown("### 👍 잘한 점")
            for item in data["strengths"] or ["뚜렷한 강점을 찾기 어렵습니다."]:
                st.markdown(f"- {item}")
        with right:
            st.markdown("### 🔧 우선 보완할 점")
            for item in data["improvements"] or ["큰 보완점이 없습니다."]:
                st.markdown(f"- {item}")

        st.markdown("### 💬 AI Coach가 묻는 질문")
        if data["coach_questions"]:
            for i, q in enumerate(data["coach_questions"], 1):
                st.markdown(f"{i}. {q}")
        else:
            st.write("추가 질문 없이도 충분히 개선할 수 있습니다.")

        st.markdown("### 🎓 이번에 집중할 AI 활용 역량")
        st.write(f"**{data['capability_focus']}** — {data['capability_reason']}")
        st.markdown("### 💡 오늘의 한 줄 학습")
        st.info(data["learning_point"])

    with tab2:
        st.markdown("### 바로 복사해서 사용할 수 있는 개선 프롬프트")
        st.text_area("개선된 프롬프트", value=data["revised_prompt"], height=330, label_visibility="collapsed")

    with tab3:
        detail_labels = {
            "goal": "🎯 Goal",
            "context": "🧩 Context",
            "constraints": "📏 Constraints",
            "output": "📄 Output",
            "verification": "🔎 Verification",
        }
        for key, label in detail_labels.items():
            item = scores[key]
            with st.expander(f"{label} · {item['score']}/20", expanded=True):
                st.markdown("**평가 이유**")
                st.write(item["reason"])
                st.markdown("**개선 방법**")
                st.write(item["improvement"])

    with tab4:
        st.caption("프론트엔드 개발자가 받을 데이터 형태를 그대로 보여주는 탭입니다.")
        st.json(data)
