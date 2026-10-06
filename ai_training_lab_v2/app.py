from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from demo_mode import demo_evaluate, demo_reply
from gemini_service import chat_reply, evaluate
from missions import CATEGORIES, DIFFICULTIES, MISSIONS
from scoring import ABILITY_META, ABILITY_ORDER, all_ability_scores, biggest_growth, overall_score, strongest_assessed, update_profile, weakest_assessed

load_dotenv()
st.set_page_config(page_title="AI 역량 훈련 Lab", page_icon="Q", layout="wide")

ACCENT = "#ff5a3d"
BASELINE = {
    "ai_basic": 62,
    "ai_usage": 58,
    "human_agency": 55,
    "human_responsibility": 52,
    "ethical_view": 68,
    "safe_use": 72,
}

st.markdown(f"""
<style>
.block-container {{max-width: 1460px; padding-top: 1rem; padding-bottom: 3rem;}}
#MainMenu, footer {{visibility:hidden;}}
.q-top {{display:flex; align-items:center; gap:12px; margin-bottom:8px;}}
.q-logo {{font-weight:900; font-size:28px; color:{ACCENT};}}
.q-title {{font-size:24px; font-weight:800; color:#343842;}}
.muted {{color:#7a7f89; font-size:.94rem;}}
.card {{border:1px solid #e6e7ea; border-radius:18px; overflow:hidden; background:white; min-height:335px; margin-bottom:16px;}}
.card-hero {{height:132px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#fff3f0,#fffafa); font-size:62px;}}
.card-body {{padding:20px 20px 16px 20px;}}
.card-title {{font-size:19px; font-weight:800; color:#343842; margin-bottom:10px;}}
.card-summary {{font-size:14px; color:#666b74; line-height:1.65; height:72px; overflow:hidden;}}
.pill {{display:inline-block; border:1px solid #ececef; border-radius:999px; padding:4px 10px; font-size:12px; margin-right:6px; color:#666b74;}}
.detail-box {{border:1px solid #e7e7ea; border-radius:18px; padding:18px 20px; line-height:1.8; background:#fff;}}
.guide {{border:1px solid #f2c55c; background:#fffaf0; border-radius:16px; padding:16px 18px; color:#9a5c18;}}
.event {{border-left:5px solid {ACCENT}; background:#fff4f1; border-radius:12px; padding:14px 16px; margin:8px 0 14px 0;}}
.workspace-title {{font-size:24px; font-weight:800; margin:0;}}
.progress-chip {{display:inline-block; background:#f5f5f7; border-radius:999px; padding:5px 10px; font-size:12px; margin-right:6px;}}
.score-big {{font-size:64px; font-weight:900; line-height:1;}}
.feedback {{border:1px solid #e6e7ea; border-radius:16px; padding:18px; min-height:180px;}}
div[data-testid="stChatMessage"] {{border-radius:14px;}}
.stButton > button[kind="primary"] {{background:{ACCENT}; border-color:{ACCENT};}}
</style>
""", unsafe_allow_html=True)


def init_state():
    defaults = {
        "page": "library",
        "selected_id": None,
        "category": "전체",
        "difficulty": "전체",
        "messages": [],
        "active_events": [],
        "attempt_no": 1,
        "attempts": {},
        "outputs": {},
        "demo_mode": True,
        "baseline": deepcopy(BASELINE),
        "last_event_turn": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def api_key() -> str:
    try:
        sec = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        sec = ""
    return sec or os.getenv("GEMINI_API_KEY", "")


def models() -> tuple[str, str]:
    return os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"), os.getenv("GEMINI_EVAL_MODEL", "gemini-2.5-flash")


def mission() -> Dict[str, Any]:
    return MISSIONS[st.session_state.selected_id]


def attempt_history(mid: str) -> List[Dict[str, Any]]:
    return st.session_state.attempts.setdefault(mid, [])


def reset_attempt(keep_mission: bool = True):
    st.session_state.messages = []
    st.session_state.active_events = []
    st.session_state.outputs = {}
    st.session_state.last_event_turn = 0
    st.session_state.page = "workspace" if keep_mission else "library"


def event_list(m: Dict[str, Any]) -> List[str]:
    variants = m.get("event_variants", [[]])
    idx = (st.session_state.attempt_no - 1) % len(variants)
    return variants[idx]


def maybe_reveal_event():
    m = mission()
    all_events = event_list(m)
    turns = len([x for x in st.session_state.messages if x["role"] == "user"])
    target = min(turns // 2, len(all_events))
    while len(st.session_state.active_events) < target:
        st.session_state.active_events.append(all_events[len(st.session_state.active_events)])


def radar(profile: Dict[str, int], previous: Dict[str, int] | None = None) -> go.Figure:
    labels = [ABILITY_META[k]["label"] for k in ABILITY_ORDER]
    closed_labels = labels + [labels[0]]
    fig = go.Figure()
    if previous:
        vals = [previous[k] for k in ABILITY_ORDER]
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=closed_labels, fill="toself", name="이전 도전", opacity=.20, line=dict(width=2)))
    vals = [profile[k] for k in ABILITY_ORDER]
    fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=closed_labels, fill="toself", name="이번 도전" if previous else "현재 역량", opacity=.52, line=dict(width=3)))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100], tickvals=[20,40,60,80,100])),
        showlegend=True, height=500, margin=dict(l=85,r=85,t=40,b=35),
    )
    return fig


def sidebar():
    with st.sidebar:
        st.markdown("### 테스트 설정")
        st.session_state.demo_mode = st.toggle("토큰 없이 데모 모드", value=st.session_state.demo_mode)
        if st.session_state.demo_mode:
            st.caption("Gemini를 호출하지 않고 화면 흐름과 채점 구조를 테스트합니다.")
        else:
            if api_key(): st.success("Gemini API Key 연결됨")
            else: st.error("GEMINI_API_KEY가 필요합니다.")
        with st.expander("사전진단 샘플 점수"):
            for key in ABILITY_ORDER:
                st.session_state.baseline[key] = st.slider(ABILITY_META[key]["label"],0,100,int(st.session_state.baseline[key]),key=f"b_{key}")
        if st.button("전체 초기화", use_container_width=True):
            st.session_state.clear(); st.rerun()


def header(back=False):
    cols = st.columns([1, 5]) if back else st.columns(1)

    with cols[0]:
        st.markdown(
            '<div class="q-top"><span class="q-logo">Q</span>'
            '<span class="q-title">AI 역량 훈련</span></div>',
            unsafe_allow_html=True
        )

    if back and st.button("← 훈련 목록"):
        st.session_state.page = "library"
        st.rerun()
        st.markdown('<div class="q-top"><span class="q-logo">Q</span><span class="q-title">AI 역량 훈련</span></div>', unsafe_allow_html=True)
    if back and st.button("← 훈련 목록"):
        st.session_state.page="library"; st.rerun()


def library_page():
    header()
    st.caption("원하는 상황을 선택해 AI와 실제처럼 문제를 해결해보세요. 한 과제 안에서 새로운 조건과 문제가 계속 이어집니다.")
    st.markdown("---")
    cats = st.columns(len(CATEGORIES))
    for i, c in enumerate(CATEGORIES):
        if cats[i].button(c, use_container_width=True, type="primary" if st.session_state.category==c else "secondary", key=f"cat_{c}"):
            st.session_state.category=c; st.rerun()
    dcols = st.columns(6)
    for i, d in enumerate(DIFFICULTIES):
        if dcols[i].button(d, use_container_width=True, type="primary" if st.session_state.difficulty==d else "secondary", key=f"dif_{d}"):
            st.session_state.difficulty=d; st.rerun()
    st.markdown("")
    items = [m for m in MISSIONS.values() if (st.session_state.category=="전체" or m["category"]==st.session_state.category) and (st.session_state.difficulty=="전체" or m["difficulty"]==st.session_state.difficulty)]
    for start in range(0, len(items), 3):
        cols = st.columns(3, gap="large")
        for col, m in zip(cols, items[start:start+3]):
            with col:
                st.markdown(f"""
                <div class="card">
                  <div class="card-hero">{m['emoji']}</div>
                  <div class="card-body">
                    <div class="card-title">{m['title']}</div>
                    <div class="card-summary">{m['summary']}</div>
                    <div style="margin-top:12px"><span class="pill">{m['category']}</span><span class="pill">{m['difficulty']}</span><span class="pill">⏱ {m['minutes']}분</span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("훈련 시작하기", use_container_width=True, key=f"open_{m['id']}"):
                    st.session_state.selected_id=m["id"]
                    st.session_state.attempt_no=len(attempt_history(m["id"]))+1
                    st.session_state.page="detail"; st.rerun()


def detail_page():
    m=mission(); header(back=True)
    st.markdown(f"## {m['emoji']} {m['title']}")
    st.caption("과제 내용을 확인하고 훈련을 시작하세요")
    st.markdown("---")
    st.markdown("### 한 줄 요약")
    st.write(m["summary"])
    st.markdown("### 📄 상황")
    st.markdown(f'<div class="detail-box">{m["situation"]}</div>', unsafe_allow_html=True)
    st.markdown("### 🎯 수행 목표")
    for i,g in enumerate(m["goals"],1): st.markdown(f"**{i}.** {g}")
    st.markdown("### ❕ 제약 조건")
    for c in m["constraints"]: st.markdown(f"- {c}")
    st.markdown("### 💡 시작 가이드")
    st.markdown(f'<div class="guide">{m["start_guide"]}</div>', unsafe_allow_html=True)
    st.caption("※ 훈련 모드에서는 시작 가이드를 제공합니다. 진단 모드에서는 숨길 수 있습니다.")
    st.markdown("")
    b1,b2=st.columns(2)
    if b1.button("다시 선택하기", use_container_width=True): st.session_state.page="library"; st.rerun()
    if b2.button("시작하기", type="primary", use_container_width=True):
        reset_attempt(True); st.rerun()


def task_panel(m: Dict[str,Any]):
    st.markdown("#### 👁 상세 과제 보기")
    with st.container(height=260, border=True):
        st.markdown(m["situation"])
        st.markdown("**수행 목표**")
        for i,g in enumerate(m["goals"],1): st.write(f"{i}. {g}")
        st.markdown("**제약 조건**")
        for c in m["constraints"]: st.write(f"• {c}")


def workspace_page():
    m=mission(); maybe_reveal_event()
    top1, top2, top3 = st.columns([6,1,1])
    with top1:
        st.markdown(f'<div class="workspace-title">{m["emoji"]} {m["title"]} <span class="muted">{m["difficulty"]} · ⏱ {m["minutes"]}분</span></div>', unsafe_allow_html=True)
    if top2.button("포기하기", use_container_width=True): st.session_state.page="library"; st.rerun()
    st.markdown("---")
    left,right=st.columns([1.05,1], gap="small")
    with left:
        st.markdown("#### 💬 AI와 대화하기")
        st.markdown(f'<div class="guide"><b>시작 가이드</b><br>{m["start_guide"]}</div>', unsafe_allow_html=True)
        if st.session_state.active_events:
            st.markdown(f'<div class="event"><b>🔔 새로운 상황 {len(st.session_state.active_events)}</b><br>{st.session_state.active_events[-1]}</div>', unsafe_allow_html=True)
        chatbox=st.container(height=520, border=True)
        with chatbox:
            if not st.session_state.messages:
                st.markdown('<div class="muted" style="text-align:center;margin-top:170px;">🤖<br><br>AI와 대화를 시작해보세요</div>', unsafe_allow_html=True)
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
        prompt=st.chat_input("메시지를 입력하세요...", key=f"chat_{m['id']}_{st.session_state.attempt_no}")
        if prompt:
            st.session_state.messages.append({"role":"user","content":prompt})
            maybe_reveal_event()
            try:
                if st.session_state.demo_mode:
                    ans=demo_reply(prompt,m,st.session_state.active_events)
                else:
                    if not api_key(): st.error("GEMINI_API_KEY가 필요합니다."); st.stop()
                    cm,_=models(); ans=chat_reply(api_key(),cm,m,st.session_state.active_events,st.session_state.messages)
                st.session_state.messages.append({"role":"assistant","content":ans})
                st.rerun()
            except Exception as e: st.error(f"Gemini 응답 오류: {e}")
    with right:
        task_panel(m)
        st.markdown("#### 📄 결과물 작성하기")
        st.caption(m["deliverable_intro"])
        with st.container(height=510, border=True):
            st.markdown(f"### {m['deliverable_title']}")
            for key,label,ph in m["output_sections"]:
                state_key=f"out_{m['id']}_{st.session_state.attempt_no}_{key}"
                val=st.text_area(label, value=st.session_state.outputs.get(key,""), placeholder=ph, height=100, key=state_key)
                st.session_state.outputs[key]=val
    st.markdown("---")
    user_turns=len([x for x in st.session_state.messages if x["role"]=="user"])
    filled=sum(bool(v.strip()) for v in st.session_state.outputs.values())
    c1,c2,c3=st.columns([2,2,1])
    with c1:
        st.markdown(f'<span class="progress-chip">대화 {user_turns}회</span><span class="progress-chip">파생 상황 {len(st.session_state.active_events)}/{len(event_list(m))}</span><span class="progress-chip">결과물 {filled}/{len(m["output_sections"])}</span>', unsafe_allow_html=True)
    if c3.button("제출하기", type="primary", use_container_width=True, disabled=user_turns==0 or filled==0):
        with st.spinner("전체 대화와 결과물을 분석하고 있어요..."):
            try:
                if st.session_state.demo_mode:
                    result=demo_evaluate(st.session_state.messages, st.session_state.outputs, st.session_state.active_events, m)
                else:
                    if not api_key(): st.error("GEMINI_API_KEY가 필요합니다."); st.stop()
                    _,em=models(); result=evaluate(api_key(),em,m,st.session_state.active_events,st.session_state.messages,st.session_state.outputs)
                hist=attempt_history(m["id"])
                base = hist[-1]["profile"] if hist else st.session_state.baseline
                prof=update_profile(base,result)
                hist.append({"attempt_no":st.session_state.attempt_no,"result":result,"overall":overall_score(result),"profile":prof,"messages":deepcopy(st.session_state.messages),"events":deepcopy(st.session_state.active_events),"outputs":deepcopy(st.session_state.outputs)})
                st.session_state.page="result"; st.rerun()
            except Exception as e: st.error(f"평가 오류: {e}")


def result_page():
    m=mission(); hist=attempt_history(m["id"]); cur=hist[-1]; prev=hist[-2] if len(hist)>=2 else None
    st.markdown(f"## {m['emoji']} {m['title']} · 결과")
    a,b=st.columns([.65,1.35], gap="large")
    with a:
        st.caption("이번 수행 점수")
        st.markdown(f'<div class="score-big">{cur["overall"]}<span style="font-size:20px">점</span></div>', unsafe_allow_html=True)
        if prev:
            d=cur["overall"]-prev["overall"]; st.markdown(f"### 이전 도전보다 {d:+d}점")
        else: st.caption("첫 번째 도전입니다.")
        st.markdown("#### 역량별 결과")
        scores=all_ability_scores(cur["result"])
        for k in ABILITY_ORDER:
            if scores[k] is None: st.write(f"{ABILITY_META[k]['label']}: **이번 미션 미평가**")
            else: st.write(f"{ABILITY_META[k]['label']}: **{scores[k]}점**")
    with b:
        st.plotly_chart(radar(cur["profile"], prev["profile"] if prev else st.session_state.baseline), use_container_width=True, config={"displayModeBar":False})
    s=strongest_assessed(cur["result"]); w=weakest_assessed(cur["result"])
    f1,f2,f3=st.columns(3)
    with f1:
        st.markdown('<div class="feedback"><h3>👍 가장 잘한 점</h3>',unsafe_allow_html=True)
        if s: st.markdown(f"**{s[0]} · {s[1]}점**")
        st.write(cur["result"].get("strength_feedback","")); st.markdown('</div>',unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feedback"><h3>🔍 보완할 점</h3>',unsafe_allow_html=True)
        if w: st.markdown(f"**{w[0]} · {w[1]}점**")
        st.write(cur["result"].get("improvement_feedback","")); st.markdown('</div>',unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feedback"><h3>🎯 다음 도전에서</h3>',unsafe_allow_html=True)
        st.write(cur["result"].get("next_action","")); st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("### 파생 상황 대응")
    st.info(cur["result"].get("event_feedback","이번 과제에서 추가된 상황에 대한 대응을 분석했습니다."))
    st.markdown("### 최종 결과물 피드백")
    st.info(cur["result"].get("deliverable_feedback","최종 결과물의 완성도와 사용자 판단을 확인했습니다."))
    if prev:
        g=biggest_growth(prev["result"],cur["result"])
        if g: st.success(f"가장 많이 성장한 역량: **{g[0]} {g[1]} → {g[2]} ({g[3]:+d})**")
    with st.expander("평가 근거 자세히 보기"):
        for k in ABILITY_ORDER:
            block=cur["result"].get(k,{})
            st.markdown(f"#### {ABILITY_META[k]['label']}")
            if not block.get("evaluated",False): st.caption("이번 과제에서는 충분히 관찰되지 않았습니다."); continue
            for ev in block.get("evidence",[]): st.write(f"- {ev}")
            st.caption(block.get("feedback",""))
    st.markdown("---")
    c1,c2,c3=st.columns(3)
    if c1.button("🔄 다른 조건으로 다시 도전", type="primary", use_container_width=True):
        st.session_state.attempt_no=len(hist)+1; reset_attempt(True); st.rerun()
    if c2.button("대화/결과물 다시 보기", use_container_width=True): st.session_state.page="review"; st.rerun()
    if c3.button("다른 훈련 선택", use_container_width=True): st.session_state.page="library"; st.rerun()


def review_page():
    m=mission(); cur=attempt_history(m["id"])[-1]
    st.markdown(f"## {m['title']} · 수행 기록")
    l,r=st.columns(2)
    with l:
        st.markdown("### AI 대화")
        for msg in cur["messages"]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if cur["events"]:
            st.markdown("### 공개된 파생 상황")
            for i,e in enumerate(cur["events"],1): st.write(f"{i}. {e}")
    with r:
        st.markdown("### 최종 결과물")
        for key,label,_ in m["output_sections"]:
            st.markdown(f"**{label}**")
            st.write(cur["outputs"].get(key,"") or "—")
    if st.button("← 결과로 돌아가기"): st.session_state.page="result"; st.rerun()


init_state(); sidebar()
if st.session_state.page=="library": library_page()
elif st.session_state.page=="detail": detail_page()
elif st.session_state.page=="workspace": workspace_page()
elif st.session_state.page=="result": result_page()
else: review_page()
