from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from demo_mode import demo_assistant_reply, demo_evaluate
from gemini_service import chat_once, evaluate_conversation
from scoring import (
    ABILITY_META,
    ABILITY_ORDER,
    all_ability_scores,
    biggest_growth,
    evaluated_labels,
    overall_score,
    strongest_assessed,
    update_profile,
    weakest_assessed,
)

load_dotenv()

st.set_page_config(
    page_title="AI 역량 훈련 - 부산 미션",
    page_icon="🧭",
    layout="wide",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .block-container {max-width: 1320px; padding-top: 1.5rem; padding-bottom: 3rem;}
    .mission-card {padding: 1.25rem 1.35rem; border: 1px solid rgba(49,51,63,.18); border-radius: 18px; background: rgba(250,250,252,.7);}
    .small-muted {color: #6b7280; font-size: .92rem;}
    .score-big {font-size: 3.6rem; font-weight: 800; line-height: 1; margin-bottom: .4rem;}
    .delta-up {font-size: 1.05rem; font-weight: 700;}
    .feedback-card {padding: 1rem 1.1rem; border: 1px solid rgba(49,51,63,.14); border-radius: 14px; margin-bottom: .75rem;}
    div[data-testid="stChatMessage"] {border-radius: 14px;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Constants ----------
DEFAULT_BASELINE = {
    "ai_basic": 62,
    "ai_usage": 58,
    "human_agency": 55,
    "human_responsibility": 52,
    "ethical_view": 68,
    "safe_use": 72,
}

MISSION_TITLE = "친구들과 부산 2박 3일 여행을 계획해보세요"
MISSION_BULLETS = [
    "대학생 친구 4명",
    "11월 금요일~일요일, 2박 3일",
    "서울 출발 · 자동차 없음",
    "1인당 최대 예산 30만 원",
    "맛집과 관광을 모두 즐기고 싶음",
    "일요일 저녁 서울 복귀",
]


# ---------- Session state ----------
def init_state() -> None:
    defaults = {
        "phase": "mission",
        "messages": [],
        "interaction_id": None,
        "attempts": [],
        "attempt_no": 1,
        "demo_mode": True,
        "baseline_profile": deepcopy(DEFAULT_BASELINE),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_current_attempt() -> None:
    st.session_state.messages = []
    st.session_state.interaction_id = None
    st.session_state.phase = "mission"


init_state()


# ---------- Helpers ----------
def get_api_key() -> str:
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("GEMINI_API_KEY", "")


def current_models() -> tuple[str, str]:
    chat_model = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.8-flash")
    eval_model = os.getenv("GEMINI_EVAL_MODEL", "gemini-3.8-flash")
    return chat_model, eval_model


def profile_for_attempt(result: Dict[str, Any]) -> Dict[str, int]:
    return update_profile(st.session_state.baseline_profile, result)


def radar_figure(
    current_profile: Dict[str, int],
    previous_profile: Dict[str, int] | None = None,
    title: str = "6가지 AI 역량 프로필",
) -> go.Figure:
    labels = [ABILITY_META[k]["label"] for k in ABILITY_ORDER]
    current_vals = [current_profile[k] for k in ABILITY_ORDER]
    labels_closed = labels + [labels[0]]
    current_closed = current_vals + [current_vals[0]]

    fig = go.Figure()
    if previous_profile:
        prev_vals = [previous_profile[k] for k in ABILITY_ORDER]
        fig.add_trace(
            go.Scatterpolar(
                r=prev_vals + [prev_vals[0]],
                theta=labels_closed,
                fill="toself",
                name="이전 도전",
                opacity=0.28,
                line=dict(width=2),
            )
        )

    fig.add_trace(
        go.Scatterpolar(
            r=current_closed,
            theta=labels_closed,
            fill="toself",
            name="이번 도전" if previous_profile else "현재 프로필",
            opacity=0.58,
            line=dict(width=3),
        )
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[20, 40, 60, 80, 100]),
        ),
        showlegend=True,
        height=520,
        margin=dict(l=90, r=90, t=70, b=50),
    )
    return fig


def render_mission_card() -> None:
    bullets = "".join([f"<li>{b}</li>" for b in MISSION_BULLETS])
    st.markdown(
        f"""
        <div class="mission-card">
          <div class="small-muted">MISSION 01 · 실전 AI 활용 훈련</div>
          <h2 style="margin:.45rem 0 .7rem 0;">{MISSION_TITLE}</h2>
          <ul>{bullets}</ul>
          <hr style="border:none;border-top:1px solid rgba(49,51,63,.12);margin:1rem 0;"/>
          <b>목표</b><br/>
          AI를 자유롭게 활용하여 친구들에게 실제로 공유할 수 있는 여행 계획을 완성하세요.<br/>
          <span class="small-muted">AI와 몇 번을 대화해도 괜찮습니다. 계획이 완성됐다고 생각하면 제출해주세요.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_baseline_sidebar() -> None:
    with st.sidebar:
        st.header("테스트 설정")
        st.session_state.demo_mode = st.toggle(
            "토큰 없이 데모 모드",
            value=st.session_state.demo_mode,
            help="켜면 Gemini API를 호출하지 않고 화면·평가 흐름만 테스트합니다.",
        )
        if st.session_state.demo_mode:
            st.caption("현재: 데모 응답 + 간단한 행동 기반 모의 채점")
        else:
            st.caption("현재: 실제 Gemini 채팅 + Gemini 평가")
            if not get_api_key():
                st.error("GEMINI_API_KEY가 없습니다. .env 또는 Streamlit Secrets에 추가하세요.")

        with st.expander("사전진단 샘플 점수", expanded=False):
            st.caption("기존 사전진단 페이지와 연결할 때는 이 값을 실제 진단 점수로 넘기면 됩니다.")
            for key in ABILITY_ORDER:
                st.session_state.baseline_profile[key] = st.slider(
                    ABILITY_META[key]["label"],
                    0,
                    100,
                    int(st.session_state.baseline_profile[key]),
                    key=f"baseline_{key}",
                )

        st.divider()
        if st.button("전체 테스트 초기화", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# ---------- Mission page ----------
def mission_page() -> None:
    st.title("AI 역량 훈련")
    st.caption(f"도전 {st.session_state.attempt_no}회차 · 답을 맞히는 시험이 아니라 AI를 사용하는 과정을 평가합니다.")

    left, right = st.columns([0.9, 1.45], gap="large")

    with left:
        render_mission_card()
        st.markdown("### 진행 방법")
        st.markdown("AI에게 자유롭게 요청하고, 결과를 보고 필요하면 계속 수정하세요. **평가 기준은 문제 화면에 노출하지 않습니다.**")
        if st.session_state.attempt_no > 1 and st.session_state.attempts:
            last = st.session_state.attempts[-1]["result"]
            st.info(f"이전 피드백 한 가지: {last.get('next_action', '')}")

    with right:
        st.subheader("AI와 대화하기")
        chat_box = st.container(height=560, border=True)
        with chat_box:
            if not st.session_state.messages:
                with st.chat_message("assistant"):
                    st.write("여행 계획을 함께 만들어볼게요. 무엇부터 정해볼까요?")
            else:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        prompt = st.chat_input("AI에게 요청해보세요", key=f"chat_input_{st.session_state.attempt_no}")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                if st.session_state.demo_mode:
                    turn = len([m for m in st.session_state.messages if m["role"] == "user"])
                    answer = demo_assistant_reply(prompt, turn)
                else:
                    api_key = get_api_key()
                    if not api_key:
                        st.error("GEMINI_API_KEY가 필요합니다.")
                        st.stop()
                    chat_model, _ = current_models()
                    answer, interaction_id = chat_once(
                        api_key=api_key,
                        model=chat_model,
                        user_text=prompt,
                        previous_interaction_id=st.session_state.interaction_id,
                    )
                    st.session_state.interaction_id = interaction_id
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as exc:
                st.error(f"AI 응답 중 오류가 발생했습니다: {exc}")

        st.markdown("")
        submit_disabled = len([m for m in st.session_state.messages if m["role"] == "user"]) == 0
        if st.button(
            "최종 결과 제출하기",
            type="primary",
            use_container_width=True,
            disabled=submit_disabled,
        ):
            with st.spinner("대화 과정을 분석하고 있어요..."):
                try:
                    if st.session_state.demo_mode:
                        result = demo_evaluate(st.session_state.messages)
                    else:
                        api_key = get_api_key()
                        if not api_key:
                            st.error("GEMINI_API_KEY가 필요합니다.")
                            st.stop()
                        _, eval_model = current_models()
                        result = evaluate_conversation(
                            api_key=api_key,
                            model=eval_model,
                            messages=st.session_state.messages,
                        )

                    attempt = {
                        "attempt_no": st.session_state.attempt_no,
                        "messages": deepcopy(st.session_state.messages),
                        "result": result,
                        "overall": overall_score(result),
                        "profile": profile_for_attempt(result),
                    }
                    st.session_state.attempts.append(attempt)
                    st.session_state.phase = "result"
                    st.rerun()
                except Exception as exc:
                    st.error(f"평가 중 오류가 발생했습니다: {exc}")


# ---------- Result page ----------
def result_page() -> None:
    attempt = st.session_state.attempts[-1]
    result = attempt["result"]
    score = attempt["overall"]
    current_profile = attempt["profile"]
    previous_attempt = st.session_state.attempts[-2] if len(st.session_state.attempts) >= 2 else None

    st.title("이번 미션 결과")

    c1, c2 = st.columns([0.72, 1.28], gap="large")
    with c1:
        st.markdown('<div class="small-muted">종합 수행 점수</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-big">{score}<span style="font-size:1.4rem;font-weight:600;">점</span></div>', unsafe_allow_html=True)

        if previous_attempt:
            delta = score - previous_attempt["overall"]
            sign = "+" if delta >= 0 else ""
            st.markdown(f'<div class="delta-up">이전 도전보다 {sign}{delta}점</div>', unsafe_allow_html=True)
        else:
            st.caption("첫 번째 도전입니다.")

        assessed = evaluated_labels(result)
        st.markdown("#### 이번 미션에서 직접 평가된 영역")
        for label in assessed:
            st.write(f"✓ {label}")
        unassessed = [ABILITY_META[k]["label"] for k in ABILITY_ORDER if not result.get(k, {}).get("evaluated", False)]
        if unassessed:
            st.caption("미평가 영역은 사전진단 프로필 점수를 그대로 유지합니다: " + ", ".join(unassessed))

        scores = all_ability_scores(result)
        st.markdown("#### 세부 점수")
        for key in ABILITY_ORDER:
            val = scores[key]
            if val is None:
                st.write(f"{ABILITY_META[key]['label']}: **미평가**")
            else:
                st.write(f"{ABILITY_META[key]['label']}: **{val}점**")

    with c2:
        prev_profile = previous_attempt["profile"] if previous_attempt else None
        st.plotly_chart(
            radar_figure(current_profile, prev_profile),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.divider()
    f1, f2, f3 = st.columns(3, gap="medium")
    strongest = strongest_assessed(result)
    weakest = weakest_assessed(result)
    with f1:
        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
        st.markdown("### 👍 가장 잘한 점")
        if strongest:
            st.markdown(f"**{strongest[0]} · {strongest[1]}점**")
        st.write(result.get("strength_feedback", ""))
        st.markdown("</div>", unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 보완할 점")
        if weakest:
            st.markdown(f"**{weakest[0]} · {weakest[1]}점**")
        st.write(result.get("improvement_feedback", ""))
        st.markdown("</div>", unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 다음 도전에서 하나만")
        st.write(result.get("next_action", ""))
        st.markdown("</div>", unsafe_allow_html=True)

    if previous_attempt:
        growth = biggest_growth(previous_attempt["result"], result)
        if growth:
            label, prev, curr, delta = growth
            st.markdown("### 이전 도전과 비교")
            st.success(f"가장 많이 성장한 역량: **{label} {prev} → {curr} ({delta:+d})**")

    with st.expander("평가 근거 보기"):
        for key in ABILITY_ORDER:
            block = result.get(key, {})
            st.markdown(f"#### {ABILITY_META[key]['label']}")
            if not block.get("evaluated", False):
                st.caption(block.get("feedback", "이번 미션에서는 평가되지 않았습니다."))
                continue
            evidence = block.get("evidence", [])
            if evidence:
                for item in evidence:
                    st.write(f"- {item}")
            st.caption(block.get("feedback", ""))

    st.divider()
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("🔄 피드백 적용해서 다시 도전", type="primary", use_container_width=True):
            st.session_state.attempt_no += 1
            reset_current_attempt()
            st.rerun()
    with b2:
        if st.button("대화 내용 다시 보기", use_container_width=True):
            st.session_state.phase = "review"
            st.rerun()


# ---------- Review page ----------
def review_page() -> None:
    attempt = st.session_state.attempts[-1]
    st.title(f"도전 {attempt['attempt_no']}회차 대화 기록")
    for msg in attempt["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if st.button("결과 화면으로 돌아가기"):
        st.session_state.phase = "result"
        st.rerun()


# ---------- Main ----------
render_baseline_sidebar()

if st.session_state.phase == "mission":
    mission_page()
elif st.session_state.phase == "result":
    result_page()
else:
    review_page()
