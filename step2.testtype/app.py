from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from demo_mode import demo_evaluate, demo_plan, demo_reply
from gemini_service import chat_reply, create_training_plan, evaluate
from missions import CATEGORIES, MISSIONS
from scoring import (
    ABILITY_META, ABILITY_ORDER, all_ability_scores, biggest_growth,
    overall_score, strongest_assessed, update_profile, weakest_assessed,
)

load_dotenv()
st.set_page_config(page_title="AI Practice Lab", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

PRIMARY = "#635BFF"
TEAL = "#0EA5A4"
INK = "#172033"
MUTED = "#6B7280"
SURFACE = "#F6F7FB"
BASELINE = {
    "ai_basic": 62, "ai_usage": 58, "human_agency": 55,
    "human_responsibility": 52, "ethical_view": 68, "safe_use": 72,
}

st.markdown(f"""
<style>
:root {{ --primary:{PRIMARY}; --ink:{INK}; --muted:{MUTED}; --surface:{SURFACE}; }}
html, body, [class*="css"] {{ font-family: Inter, Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.block-container {{ max-width: 1440px; padding-top: 1.7rem; padding-bottom: 3rem; }}
#MainMenu, footer {{ visibility:hidden; }}
[data-testid="stSidebar"] {{ background:#F8F9FC; }}
.brand {{ display:flex; align-items:center; gap:10px; margin-bottom:22px; }}
.brand-mark {{ width:34px; height:34px; display:grid; place-items:center; border-radius:11px; color:white; background:linear-gradient(135deg,{PRIMARY},#8B7CFF); font-weight:900; }}
.brand-name {{ font-weight:850; font-size:20px; color:{INK}; letter-spacing:-.3px; }}
.hero {{ border-radius:26px; padding:36px 38px; background:linear-gradient(120deg,#171C31 0%,#27224F 58%,#234B57 100%); color:white; margin-bottom:26px; }}
.hero-kicker {{ font-size:13px; font-weight:700; opacity:.68; letter-spacing:.12em; text-transform:uppercase; }}
.hero-title {{ font-size:32px; font-weight:850; line-height:1.25; margin:10px 0 8px 0; letter-spacing:-.8px; }}
.hero-copy {{ max-width:720px; font-size:15px; color:#D8DBE8; line-height:1.7; }}
.section-title {{ font-size:22px; font-weight:850; color:{INK}; letter-spacing:-.5px; margin:14px 0 3px 0; }}
.section-copy {{ color:{MUTED}; font-size:14px; margin-bottom:16px; }}
.scenario-card {{ border:1px solid #E6E8F0; border-radius:20px; padding:22px; background:white; min-height:270px; box-shadow:0 1px 2px rgba(23,32,51,.03); }}
.scenario-number {{ width:42px; height:42px; border-radius:13px; display:grid; place-items:center; font-weight:850; background:#F0EFFF; color:{PRIMARY}; margin-bottom:20px; }}
.scenario-eyebrow {{ font-size:12px; font-weight:750; color:{PRIMARY}; margin-bottom:7px; }}
.scenario-title {{ font-size:19px; line-height:1.35; font-weight:850; color:{INK}; min-height:52px; }}
.scenario-summary {{ font-size:14px; line-height:1.68; color:{MUTED}; min-height:74px; margin-top:9px; }}
.meta {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }}
.chip {{ display:inline-block; padding:5px 9px; background:#F5F6FA; color:#646A78; border-radius:999px; font-size:12px; }}
.detail-shell {{ border:1px solid #E8E9F0; border-radius:24px; padding:28px; background:white; }}
.detail-title {{ font-size:29px; font-weight:880; color:{INK}; letter-spacing:-.8px; line-height:1.25; }}
.detail-summary {{ color:{MUTED}; line-height:1.7; margin-top:10px; }}
.info-panel {{ border-radius:18px; padding:20px; background:#F7F8FC; }}
.goal-row {{ display:flex; gap:11px; align-items:flex-start; margin:11px 0; color:#333A4D; line-height:1.55; }}
.goal-no {{ flex:0 0 auto; width:25px; height:25px; border-radius:8px; display:grid; place-items:center; font-size:12px; font-weight:800; background:#E9E7FF; color:{PRIMARY}; }}
.workspace-head {{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:14px; }}
.workspace-title {{ font-size:24px; font-weight:880; color:{INK}; letter-spacing:-.6px; }}
.phase-wrap {{ display:flex; gap:7px; flex-wrap:wrap; margin-top:8px; }}
.phase {{ font-size:12px; padding:6px 10px; border-radius:999px; background:#F0F1F5; color:#747987; }}
.phase-on {{ background:#E9E7FF; color:{PRIMARY}; font-weight:750; }}
.panel-title {{ font-size:14px; font-weight:800; color:#3A4050; margin-bottom:9px; }}
.chat-shell {{ border:1px solid #E5E7EF; border-radius:20px; padding:12px; background:white; }}
.chat-empty {{ text-align:center; color:#9297A5; padding:92px 10px; }}
.branch-card {{ border:1px solid #D8D5FF; border-radius:17px; padding:16px; background:#F8F7FF; margin:10px 0 13px 0; }}
.branch-kicker {{ font-size:11px; font-weight:850; color:{PRIMARY}; letter-spacing:.08em; }}
.branch-title {{ font-size:16px; font-weight:850; color:{INK}; margin:4px 0; }}
.branch-copy {{ font-size:13px; color:#5F6573; line-height:1.55; }}
.output-shell {{ border:1px solid #E5E7EF; border-radius:20px; padding:18px 18px 8px; background:white; }}
.progress-row {{ display:flex; gap:8px; flex-wrap:wrap; }}
.progress-pill {{ font-size:12px; padding:6px 10px; border-radius:999px; background:#F4F5F8; color:#646B78; }}
.result-score {{ font-size:68px; font-weight:900; color:{INK}; line-height:1; letter-spacing:-3px; }}
.result-sub {{ color:{MUTED}; font-size:14px; margin-top:8px; }}
.feedback-card {{ border:1px solid #E6E8EF; border-radius:18px; padding:19px; background:white; min-height:176px; }}
.feedback-label {{ font-size:12px; font-weight:850; color:{PRIMARY}; letter-spacing:.05em; }}
.feedback-title {{ font-size:17px; font-weight:850; color:{INK}; margin:8px 0; }}
.small-muted {{ color:{MUTED}; font-size:13px; line-height:1.6; }}
.stButton > button {{ border-radius:12px; font-weight:700; min-height:42px; }}
.stButton > button[kind="primary"] {{ background:{PRIMARY}; border-color:{PRIMARY}; }}
div[data-testid="stTextArea"] textarea {{ border-radius:12px; }}
div[data-testid="stChatMessage"] {{ background:#FAFAFC; border-radius:14px; padding:4px 10px; }}
@media (max-width:900px) {{ .hero {{ padding:26px; }} .hero-title {{ font-size:27px; }} }}
</style>
""", unsafe_allow_html=True)


def init_state():
    defaults = {
        "page": "library", "selected_id": None, "category": "전체",
        "messages": [], "training_plan": None, "revealed_events": [], "event_index": 0,
        "outputs": {}, "attempts": {}, "attempt_no": 1,
        "mode": "Gemini", "baseline": deepcopy(BASELINE), "draft_message": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_api_key() -> str:
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return secret or os.getenv("GEMINI_API_KEY", "")


def get_model() -> str:
    try:
        secret = st.secrets.get("GEMINI_MODEL", "")
    except Exception:
        secret = ""
    return secret or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def selected_mission() -> Dict[str, Any]:
    return MISSIONS[st.session_state.selected_id]


def histories(mid: str) -> List[Dict[str, Any]]:
    return st.session_state.attempts.setdefault(mid, [])


def render_brand(back: bool = False):
    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown('<div class="brand"><div class="brand-mark">◈</div><div class="brand-name">AI Practice Lab</div></div>', unsafe_allow_html=True)
    if back and c2.button("← 목록으로", use_container_width=True):
        st.session_state.page = "library"
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("### 실행 설정")
        options = ["Gemini", "UI 데모"]
        idx = 0 if st.session_state.mode == "Gemini" else 1
        st.session_state.mode = st.radio("모드", options, index=idx, horizontal=True)
        if st.session_state.mode == "Gemini":
            if get_api_key():
                st.success(f"Gemini 연결됨 · {get_model()}")
            else:
                st.warning("Streamlit Secrets에 GEMINI_API_KEY를 넣어주세요.")
        else:
            st.info("API 호출 없이 화면 흐름을 테스트합니다.")
        st.markdown("---")
        with st.expander("사전진단 샘플 점수"):
            for key in ABILITY_ORDER:
                st.session_state.baseline[key] = st.slider(ABILITY_META[key]["label"], 0, 100, int(st.session_state.baseline[key]), key=f"base_{key}")
        if st.button("세션 전체 초기화", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def library_page():
    render_brand()
    st.markdown('''<div class="hero"><div class="hero-kicker">PRACTICE, NOT QUIZ</div><div class="hero-title">AI를 잘 쓰는지는<br>실제 문제를 풀 때 드러납니다.</div><div class="hero-copy">상황을 하나 선택하고 AI와 직접 해결해보세요. 도중에 조건이 바뀌고, 정보가 흔들리고, 선택이 필요해집니다. 결과보다 ‘어떻게 AI를 사용했는지’를 분석합니다.</div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-title">오늘 어떤 상황을 연습할까요?</div><div class="section-copy">하나의 상황 안에서 3개의 새로운 변수가 순서대로 이어집니다.</div>', unsafe_allow_html=True)
    cols = st.columns(len(CATEGORIES))
    for i, cat in enumerate(CATEGORIES):
        if cols[i].button(cat, use_container_width=True, type="primary" if st.session_state.category == cat else "secondary", key=f"cat_{cat}"):
            st.session_state.category = cat
            st.rerun()
    st.write("")
    missions = [m for m in MISSIONS.values() if st.session_state.category == "전체" or m["eyebrow"].startswith(st.session_state.category)]
    for start in range(0, len(missions), 3):
        row = st.columns(3, gap="large")
        for col, m in zip(row, missions[start:start+3]):
            with col:
                st.markdown(f'''<div class="scenario-card"><div class="scenario-number">{m['accent']}</div><div class="scenario-eyebrow">{m['eyebrow']}</div><div class="scenario-title">{m['title']}</div><div class="scenario-summary">{m['summary']}</div><div class="meta"><span class="chip">{m['difficulty']}</span><span class="chip">약 {m['minutes']}분</span><span class="chip">변수 3개</span></div></div>''', unsafe_allow_html=True)
                if st.button("이 상황 연습하기 →", key=f"open_{m['id']}", use_container_width=True):
                    st.session_state.selected_id = m["id"]
                    st.session_state.attempt_no = len(histories(m["id"])) + 1
                    st.session_state.page = "detail"
                    st.rerun()


def detail_page():
    m = selected_mission()
    render_brand(back=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown(f'<div class="detail-title">{m["title"]}</div><div class="detail-summary">{m["summary"]}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("#### 지금 놓인 상황")
        st.markdown(f'<div class="info-panel">{m["situation"]}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("#### 이번 연습에서 완성할 것")
        for i, goal in enumerate(m["goals"], 1):
            st.markdown(f'<div class="goal-row"><div class="goal-no">{i}</div><div>{goal}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="detail-shell">', unsafe_allow_html=True)
        st.markdown("#### 기본 조건")
        for x in m["constraints"]:
            st.markdown(f"- {x}")
        st.markdown("---")
        st.markdown("#### 진행 방식")
        st.markdown("AI와 자유롭게 대화합니다. 대화 중 **3개의 새로운 상황**이 순서대로 열립니다. 마지막에는 AI 답변을 복사하는 대신, 오른쪽 결과 영역에서 직접 최종안을 정리합니다.")
        st.markdown("---")
        if st.session_state.mode == "Gemini" and not get_api_key():
            st.error("Gemini 모드로 시작하려면 Streamlit Secrets에 `GEMINI_API_KEY`가 필요합니다.")
        start_ok = st.session_state.mode == "UI 데모" or bool(get_api_key())
        if st.button("훈련 시작", type="primary", use_container_width=True, disabled=not start_ok):
            start_training(m)
        st.markdown('</div>', unsafe_allow_html=True)


def start_training(m: Dict[str, Any]):
    st.session_state.messages = []
    st.session_state.revealed_events = []
    st.session_state.event_index = 0
    st.session_state.outputs = {}
    st.session_state.draft_message = ""
    with st.spinner("이번 도전의 상황을 구성하고 있어요..."):
        try:
            if st.session_state.mode == "Gemini":
                plan = create_training_plan(get_api_key(), get_model(), m, st.session_state.attempt_no)
            else:
                plan = demo_plan(m)
        except Exception as exc:
            st.error(f"Gemini에서 훈련 상황을 만드는 중 오류가 발생했습니다: {exc}")
            return
    st.session_state.training_plan = plan
    st.session_state.messages = [{"role": "assistant", "content": plan["opening_message"]}]
    st.session_state.page = "workspace"
    st.rerun()


def reveal_next_event():
    plan = st.session_state.training_plan or {}
    events = plan.get("events", [])
    idx = st.session_state.event_index
    if idx < len(events):
        event = events[idx]
        st.session_state.revealed_events.append(event)
        st.session_state.event_index += 1
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**새로운 상황 — {event['title']}**\n\n{event['situation']}\n\n**지금 해결할 것:** {event['task']}"
        })
        st.rerun()


def send_message(m: Dict[str, Any]):
    prompt = st.session_state.get("draft_message", "").strip()
    if not prompt:
        return
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.draft_message = ""
    with st.spinner("Gemini가 생각하고 있어요..."):
        try:
            if st.session_state.mode == "Gemini":
                answer = chat_reply(get_api_key(), get_model(), m, st.session_state.revealed_events, st.session_state.messages)
            else:
                answer = demo_reply(prompt, m, st.session_state.revealed_events)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as exc:
            st.session_state.messages.append({"role": "assistant", "content": f"응답을 불러오지 못했어요: {exc}"})
    st.rerun()


def workspace_page():
    m = selected_mission()
    if not st.session_state.training_plan:
        st.session_state.page = "detail"
        st.rerun()
    render_brand()
    user_turns = sum(1 for x in st.session_state.messages if x["role"] == "user")
    unlocked = st.session_state.event_index
    phase_index = min(unlocked, 3)
    phases = ["기본 상황", "변수 1", "변수 2", "변수 3", "최종 정리"]
    st.markdown(f'<div class="workspace-head"><div><div class="workspace-title">{m["title"]}</div><div class="phase-wrap">' + ''.join(f'<span class="phase {"phase-on" if i <= phase_index else ""}">{p}</span>' for i,p in enumerate(phases)) + '</div></div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.12, .88], gap="large")
    with left:
        st.markdown('<div class="panel-title">AI와 협업하기</div>', unsafe_allow_html=True)
        with st.container(height=520, border=False):
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        st.text_area("메시지", key="draft_message", placeholder="Gemini에게 요청하거나, 답변을 검토하고 다음 지시를 내려보세요.", height=92, label_visibility="collapsed")
        send_col, event_col = st.columns([1.3,1])
        if send_col.button("Gemini에게 보내기", type="primary", use_container_width=True):
            send_message(m)
        plan_events = (st.session_state.training_plan or {}).get("events", [])
        can_open = user_turns >= max(1, st.session_state.event_index + 1) and st.session_state.event_index < len(plan_events)
        if event_col.button(
            f"새 상황 열기 ({st.session_state.event_index+1}/3)" if st.session_state.event_index < 3 else "새 상황 모두 확인",
            use_container_width=True,
            disabled=not can_open,
        ):
            reveal_next_event()
        if st.session_state.revealed_events:
            e = st.session_state.revealed_events[-1]
            st.markdown(f'<div class="branch-card"><div class="branch-kicker">CURRENT CHALLENGE</div><div class="branch-title">{e["title"]}</div><div class="branch-copy">{e["situation"]}<br><b>{e["task"]}</b></div></div>', unsafe_allow_html=True)
        else:
            st.caption("AI와 한 번 이상 대화하면 첫 번째 새로운 상황을 열 수 있어요.")

    with right:
        st.markdown('<div class="panel-title">나의 최종안</div>', unsafe_allow_html=True)
        with st.expander("현재 과제 조건 다시 보기"):
            st.write(m["situation"])
            for x in m["constraints"]:
                st.write(f"• {x}")
        st.markdown('<div class="output-shell">', unsafe_allow_html=True)
        for key, label, placeholder in m["deliverable"]:
            widget_key = f"out_{m['id']}_{st.session_state.attempt_no}_{key}"
            value = st.text_area(label, value=st.session_state.outputs.get(key, ""), placeholder=placeholder, height=112, key=widget_key)
            st.session_state.outputs[key] = value
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    filled = sum(bool(v.strip()) for v in st.session_state.outputs.values())
    st.markdown(f'<div class="progress-row"><span class="progress-pill">대화 {user_turns}회</span><span class="progress-pill">새 상황 {len(st.session_state.revealed_events)}/3</span><span class="progress-pill">최종안 {filled}/{len(m["deliverable"])}</span></div>', unsafe_allow_html=True)
    a,b,c = st.columns([1,1,1.2])
    if a.button("← 과제 설명", use_container_width=True):
        st.session_state.page = "detail"
        st.rerun()
    if b.button("처음부터 다시", use_container_width=True):
        start_training(m)
    submit_ready = user_turns >= 1 and filled >= 1
    if c.button("분석하고 결과 보기", type="primary", use_container_width=True, disabled=not submit_ready):
        submit_training(m)


def submit_training(m: Dict[str, Any]):
    with st.spinner("대화 방식과 최종안을 분석하고 있어요..."):
        try:
            if st.session_state.mode == "Gemini":
                result = evaluate(get_api_key(), get_model(), m, st.session_state.revealed_events, st.session_state.messages, st.session_state.outputs)
            else:
                result = demo_evaluate(st.session_state.messages, st.session_state.outputs, st.session_state.revealed_events, m)
        except Exception as exc:
            st.error(f"평가 중 오류가 발생했습니다: {exc}")
            return
    hist = histories(m["id"])
    base_profile = hist[-1]["profile"] if hist else st.session_state.baseline
    profile = update_profile(base_profile, result)
    hist.append({
        "attempt_no": st.session_state.attempt_no,
        "result": result,
        "overall": overall_score(result),
        "profile": profile,
        "messages": deepcopy(st.session_state.messages),
        "events": deepcopy(st.session_state.revealed_events),
        "outputs": deepcopy(st.session_state.outputs),
    })
    st.session_state.page = "result"
    st.rerun()


def radar(profile: Dict[str, int], comparison: Dict[str, int] | None = None) -> go.Figure:
    labels = [ABILITY_META[k]["label"] for k in ABILITY_ORDER]
    theta = labels + [labels[0]]
    fig = go.Figure()
    if comparison:
        vals = [comparison[k] for k in ABILITY_ORDER]
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=theta, fill="toself", name="이전", line=dict(color="#A6A9B6", width=2), fillcolor="rgba(166,169,182,.10)"))
    vals = [profile[k] for k in ABILITY_ORDER]
    fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=theta, fill="toself", name="현재", line=dict(color=PRIMARY, width=3), fillcolor="rgba(99,91,255,.16)"))
    fig.update_layout(
        polar=dict(
            bgcolor="white",
            radialaxis=dict(visible=True, range=[0,100], tickvals=[20,40,60,80,100], tickfont=dict(size=9, color="#9B9EAA"), gridcolor="#ECEEF4"),
            angularaxis=dict(gridcolor="#E6E8EF", tickfont=dict(size=12, color="#404657")),
        ),
        paper_bgcolor="white", plot_bgcolor="white", showlegend=True, height=500,
        margin=dict(l=80,r=80,t=40,b=40), legend=dict(orientation="h", y=1.08, x=.02),
    )
    return fig


def result_page():
    m = selected_mission()
    hist = histories(m["id"])
    cur = hist[-1]
    prev = hist[-2] if len(hist) >= 2 else None
    render_brand()
    st.markdown(f'<div class="section-title">{m["title"]} · 수행 분석</div><div class="section-copy">정답보다 AI를 사용한 과정에서 드러난 행동을 봅니다.</div>', unsafe_allow_html=True)
    a,b = st.columns([.7,1.3], gap="large")
    with a:
        st.markdown("### 이번 수행")
        st.markdown(f'<div class="result-score">{cur["overall"]}<span style="font-size:20px;letter-spacing:0">점</span></div>', unsafe_allow_html=True)
        if prev:
            delta = cur["overall"] - prev["overall"]
            st.markdown(f'<div class="result-sub">이전 도전보다 <b>{delta:+d}점</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-sub">첫 번째 도전입니다.</div>', unsafe_allow_html=True)
        st.write("")
        scores = all_ability_scores(cur["result"])
        for key in ABILITY_ORDER:
            label = ABILITY_META[key]["label"]
            if scores[key] is None:
                st.caption(f"{label} · 이번 미션에서는 충분히 관찰되지 않음")
            else:
                st.progress(scores[key] / 100, text=f"{label}  {scores[key]}점")
    with b:
        st.plotly_chart(radar(cur["profile"], prev["profile"] if prev else st.session_state.baseline), use_container_width=True, config={"displayModeBar":False})

    strongest = strongest_assessed(cur["result"])
    weakest = weakest_assessed(cur["result"])
    f1,f2,f3 = st.columns(3, gap="medium")
    with f1:
        st.markdown(f'<div class="feedback-card"><div class="feedback-label">STRENGTH</div><div class="feedback-title">{strongest[0] if strongest else "잘한 행동"}{" · "+str(strongest[1])+"점" if strongest else ""}</div><div class="small-muted">{cur["result"].get("strength_feedback","")}</div></div>', unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div class="feedback-card"><div class="feedback-label">NEXT FOCUS</div><div class="feedback-title">{weakest[0] if weakest else "다음 보완점"}{" · "+str(weakest[1])+"점" if weakest else ""}</div><div class="small-muted">{cur["result"].get("improvement_feedback","")}</div></div>', unsafe_allow_html=True)
    with f3:
        st.markdown(f'<div class="feedback-card"><div class="feedback-label">NEXT ACTION</div><div class="feedback-title">다음 도전에서 한 가지</div><div class="small-muted">{cur["result"].get("next_action","")}</div></div>', unsafe_allow_html=True)

    if prev:
        growth = biggest_growth(prev["result"], cur["result"])
        if growth:
            st.success(f"가장 크게 달라진 영역: **{growth[0]} {growth[1]} → {growth[2]} ({growth[3]:+d})**")
    with st.expander("왜 이런 평가가 나왔는지 보기"):
        for key in ABILITY_ORDER:
            block = cur["result"].get(key, {})
            st.markdown(f"**{ABILITY_META[key]['label']}**")
            if not block.get("evaluated", False):
                st.caption("이번 과제에서는 판단할 근거가 충분하지 않았습니다.")
                continue
            for ev in block.get("evidence", []):
                st.write(f"- {ev}")
            st.caption(block.get("feedback", ""))
        st.markdown("---")
        st.write("**파생 상황 대응**", cur["result"].get("event_feedback", ""))
        st.write("**최종안**", cur["result"].get("deliverable_feedback", ""))

    c1,c2,c3 = st.columns(3)
    if c1.button("다른 조건으로 다시 도전", type="primary", use_container_width=True):
        st.session_state.attempt_no = len(hist) + 1
        start_training(m)
    if c2.button("수행 기록 보기", use_container_width=True):
        st.session_state.page = "review"
        st.rerun()
    if c3.button("다른 상황 선택", use_container_width=True):
        st.session_state.page = "library"
        st.rerun()


def review_page():
    m = selected_mission()
    cur = histories(m["id"])[-1]
    render_brand(back=True)
    st.markdown(f"## {m['title']} · 수행 기록")
    l,r = st.columns(2, gap="large")
    with l:
        st.markdown("### AI와 나눈 대화")
        for msg in cur["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    with r:
        st.markdown("### 내가 작성한 최종안")
        for key,label,_ in m["deliverable"]:
            st.markdown(f"**{label}**")
            st.write(cur["outputs"].get(key, "") or "—")


init_state()
render_sidebar()
page = st.session_state.page
if page == "library": library_page()
elif page == "detail": detail_page()
elif page == "workspace": workspace_page()
elif page == "result": result_page()
else: review_page()
