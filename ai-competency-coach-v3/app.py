import os
import streamlit as st

from dataset import load_framework, load_questions
from judge import get_provider

st.set_page_config(page_title="AI Competency Coach", page_icon="🧠", layout="wide")

framework = load_framework()
questions = load_questions()
comp_map = {c["id"]: c for c in framework["competencies"]}

st.title("🧠 AI Competency Coach")
st.caption("6개 AI 활용 역량을 상황형 문항으로 진단하는 프로토타입")
st.info(f"현재 Judge 모드: `{os.getenv('JUDGE_PROVIDER', 'mock')}`")

competency_id = st.selectbox(
    "평가 영역",
    [c["id"] for c in framework["competencies"]],
    format_func=lambda cid: f"{comp_map[cid]['domain']} · {comp_map[cid]['name']}"
)

qs = [q for q in questions if q["competency_id"] == competency_id]
question_id = st.selectbox(
    "문항",
    [q["question_id"] for q in qs],
    format_func=lambda qid: f"{qid} · {next(q['domain'] for q in qs if q['question_id']==qid)}"
)

q = next(q for q in qs if q["question_id"] == question_id)

st.markdown("### 상황")
st.write(q["scenario"])
st.markdown("### 질문")
st.write(q["question"])

answer = st.text_area("내 답변", height=180)

if st.button("역량 평가하기", type="primary"):
    if not answer.strip():
        st.warning("답변을 입력해주세요.")
    else:
        try:
            result = get_provider().evaluate(question_id, answer)

            st.divider()
            st.metric("점수", f"{result.score}/3")
            st.markdown("### 판단 근거")
            st.write(result.reason)

            st.markdown("### Evidence")
            cols = st.columns(len(result.evidence))
            for col, (k, v) in zip(cols, result.evidence.items()):
                with col:
                    st.metric(k, v)

            st.markdown("### 코칭")
            st.write(result.feedback)
            st.info(result.next_step)

            st.markdown("### 개발용 JSON")
            st.json(result.model_dump())

        except Exception as e:
            st.error(f"{type(e).__name__}: {e}")
