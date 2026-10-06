
import random
import re
import streamlit as st

st.set_page_config(
    page_title="AI 활용 사전진단",
    page_icon="🤖",
    layout="centered",
)

# =========================================================
# 0. 디자인
# =========================================================
st.markdown(
    """
    <style>
    .block-container {
        max-width: 920px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    .hero {
        border: 1px solid rgba(128,128,128,.20);
        border-radius: 20px;
        padding: 20px 22px;
        margin-bottom: 14px;
        background: rgba(128,128,128,.04);
    }

    .hero-kicker {
        font-size: .83rem;
        font-weight: 700;
        color: #6b7280;
        margin-bottom: 4px;
        letter-spacing: .02em;
    }

    .app-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 4px;
    }

    .app-subtitle {
        color: #6b7280;
        margin-bottom: 0;
    }

    .progress-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 4px 0 6px 0;
        color: #6b7280;
        font-size: .9rem;
    }

    .current-card {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 16px;
        padding: 12px 14px;
        margin: 8px 0 10px 0;
        background: rgba(128,128,128,.018);
    }

    .current-label {
        font-size: .82rem;
        font-weight: 800;
        color: #6b7280;
        margin-bottom: 8px;
    }

    .mission-card {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 16px;
        padding: 16px 18px;
        margin: 8px 0 14px 0;
        background: rgba(128,128,128,.025);
    }

    .score-card {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0 18px 0;
        background: rgba(128,128,128,.025);
    }

    .result-title {
        font-size: 1.65rem;
        font-weight: 800;
        margin-bottom: .35rem;
        letter-spacing: -0.03em;
    }

    .score-number {
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 2px;
    }

    .score-label {
        color: #6b7280;
        font-size: .86rem;
        margin-bottom: 8px;
    }

    /* 선택지 버튼: 긴 문장이 ... 으로 잘리지 않고 끝까지 보이도록 */
    div.stButton > button {
        width: 100%;
        height: auto !important;
        min-height: 72px;
        text-align: left;
        border-radius: 14px;
        padding: 14px 16px;
        white-space: normal !important;
        overflow: visible !important;
        align-items: center;
    }

    div.stButton > button div[data-testid="stMarkdownContainer"] {
        width: 100%;
        overflow: visible !important;
    }

    div.stButton > button div[data-testid="stMarkdownContainer"] p {
        margin: 0;
        width: 100%;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        display: block !important;
        -webkit-line-clamp: unset !important;
        -webkit-box-orient: initial !important;
        word-break: keep-all;
        overflow-wrap: break-word;
        line-height: 1.45;
        text-align: left;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 14px;
        padding: 12px 14px;
        background: rgba(128,128,128,.02);
    }

    div[data-testid="stExpander"] {
        border-radius: 14px;
    }

    textarea {
        border-radius: 12px !important;
    }

    .small-note {
        color: #6b7280;
        font-size: 0.9rem;
    }

    /* 현재 질문 내부 스크롤 카드 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 1. 평가 기준
# =========================================================
DOMAINS = {
    "agency": "인간의 주도권",
    "responsibility": "인간의 책임",
    "ethics": "윤리적 관점",
    "safety": "안전하고 책임 있는 사용",
    "ai_basics": "AI의 기초",
    "utilization": "활용 능력",
}

DOMAIN_TIPS = {
    "agency": "AI에게 결정을 넘기기보다, 내가 먼저 목적과 범위를 정한 뒤 필요한 부분에 AI를 활용해보세요.",
    "responsibility": "AI가 제시한 정보는 원자료·공식 출처를 확인하고, 중요한 최종 판단은 직접 내려보세요.",
    "ethics": "정확도뿐 아니라 편향, 차별, 포용성, 타인의 권리에 미치는 영향도 함께 살펴보세요.",
    "safety": "개인정보나 저작권이 포함될 수 있는 자료는 AI에 입력하거나 공유하기 전에 위험 요소를 먼저 확인해보세요.",
    "ai_basics": "AI의 자연스러운 문장이나 자신감 있는 표현이 사실성을 보장하지 않는다는 점을 기억하세요.",
    "utilization": "목적·맥락·조건·원하는 출력 형태를 알려주고, 첫 답변이 부족하면 구체적으로 수정 요청해보세요.",
}

# =========================================================
# 2. Session State
# =========================================================
def init_state():
    defaults = {
        "stage": 0,
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "안녕하세요! 👋\n\n"
                    "몇 가지 상황을 같이 해결하면서 **평소 AI를 어떻게 활용하고 있는지** 알아볼게요.\n\n"
                    "시험처럼 정답을 맞히기보다, **실제로 평소에 할 것 같은 행동**을 선택하거나 입력해주세요."
                ),
            }
        ],
        "answers": {},
        "scores": {key: 0.0 for key in DOMAINS},
        "option_orders": {},
        "result_ready": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

# =========================================================
# 3. 공통 함수
# =========================================================
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def shuffled_once(key, items):
    """선택지 순서를 세션 동안 한 번만 섞어서 정답 위치 추측을 줄인다."""
    if key not in st.session_state.option_orders:
        copied = list(items)
        random.shuffle(copied)
        st.session_state.option_orders[key] = copied
    return st.session_state.option_orders[key]


def set_stage(stage):
    st.session_state.stage = stage
    st.rerun()


def save_choice(answer_key, label, score_key=None, score=None):
    st.session_state.answers[answer_key] = label
    add_message("user", label)
    if score_key is not None and score is not None:
        st.session_state.scores[score_key] = float(score)


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def keyword_hits(text, keyword_groups):
    """
    keyword_groups 예:
    [["출처", "원문"], ["확인", "검증"]]
    각 그룹에서 하나 이상 등장한 그룹 수를 반환.
    """
    t = normalize(text)
    hits = 0
    for group in keyword_groups:
        if any(k.lower() in t for k in group):
            hits += 1
    return hits


def score_responsibility_reason(text):
    """
    자유응답은 정답 키워드 하나만 찾는 것이 아니라,
    ① 원출처/공식자료 ② 실제 수치/맥락 확인 ③ AI 외부에서 검증
    세 요소를 대략적으로 본다.
    """
    groups = [
        ["원자료", "원문", "공식", "사이트", "보고서", "논문", "출처"],
        ["수치", "통계", "조사", "표본", "맥락", "연도", "실제", "맞는지"],
        ["직접", "검색", "찾아", "확인", "검증"],
    ]
    h = keyword_hits(text, groups)
    if h >= 3:
        return 0.5
    if h >= 1:
        return 0.25
    return 0.0


def score_ethics_reason(text):
    groups = [
        ["편향", "차별", "불공정", "공정", "불리", "유리"],
        ["학습데이터", "데이터", "과거", "출신", "학교", "성별", "연령", "배경"],
        ["권리", "포용", "다양성", "대표성"],
    ]
    h = keyword_hits(text, groups)
    if h >= 2:
        return 0.5
    if h >= 1:
        return 0.25
    return 0.0


def score_ai_basics_free(text):
    """
    '수학 노벨상' 오류를 직접 발견하면 가장 높은 보너스.
    단순히 검증 필요성만 언급하면 부분 점수.
    """
    t = normalize(text)

    math_error = (
        ("수학" in t and ("노벨" in t or "분야" in t))
        or "수학상" in t
        or "수학 분야" in t
    )

    skeptical = any(
        k in t
        for k in [
            "확인",
            "검증",
            "틀",
            "오류",
            "사실",
            "출처",
            "의심",
        ]
    )

    if math_error:
        return 0.75
    if skeptical:
        return 0.35
    return 0.0


def score_initial_prompt(text):
    """
    활용능력의 첫 요청: 최대 1점.
    길이 자체가 아니라 목적/맥락/조건/출력형태를 본다.
    """
    t = normalize(text)

    dimensions = 0

    # 목적
    if any(k in t for k in ["발표", "5분", "과제", "준비", "설명", "정리"]):
        dimensions += 1

    # 맥락 / 대상
    if any(k in t for k in ["대학", "수업", "학생", "비전공", "청중", "교수", "초보"]):
        dimensions += 1

    # 조건
    if any(k in t for k in ["장점", "단점", "한계", "사례", "각각", "개", "분량", "시간"]):
        dimensions += 1

    # 출력 형태
    if any(k in t for k in ["슬라이드", "목차", "표", "대본", "구성", "항목", "bullet", "불릿"]):
        dimensions += 1

    if dimensions >= 4:
        return 1.0
    if dimensions == 3:
        return 0.75
    if dimensions == 2:
        return 0.5
    if dimensions == 1:
        return 0.25
    return 0.0


def score_revision_prompt(text):
    """
    수정 요청: 최대 1점.
    첫 답변의 부족한 점을 구체적으로 지적하고
    새 조건/형식을 추가하는지를 본다.
    """
    t = normalize(text)

    specific_problem = any(
        k in t
        for k in [
            "일반적",
            "뻔",
            "구체",
            "사례",
            "부족",
            "너무",
            "추상",
            "중복",
            "어려",
            "쉽게",
        ]
    )

    new_constraint = any(
        k in t
        for k in [
            "슬라이드",
            "대본",
            "표",
            "목차",
            "사례",
            "각각",
            "3개",
            "5장",
            "비전공",
            "대학생",
            "분량",
            "시간",
            "근거",
        ]
    )

    vague_only = any(
        phrase in t
        for phrase in [
            "자세히",
            "다시 해",
            "더 잘",
            "더 좋",
            "길게",
        ]
    )

    if specific_problem and new_constraint:
        return 1.0
    if new_constraint:
        return 0.75
    if specific_problem:
        return 0.5
    if vague_only:
        return 0.25
    return 0.0


def get_level(scores):
    total = round(sum(scores.values()), 2)
    minimum = min(scores.values())

    # 총점 + 최소 역량 조건
    if total >= 9.5 and minimum >= 1.0:
        return 4, "주도적 활용", total
    elif total >= 6.5:
        return 3, "적용", total
    elif total >= 3.5:
        return 2, "이해", total
    else:
        return 1, "탐색", total


def scenario_number(stage):
    # 실제 화면 단계는 후속 질문 때문에 더 많지만,
    # 사용자에게는 7개 상황으로 보이게 한다.
    if stage <= 1:
        return 1
    if stage in [2, 3]:
        return 2
    if stage in [4, 5]:
        return 3
    if stage == 6:
        return 4
    if stage in [7, 8]:
        return 5
    if stage == 9:
        return 6
    if stage in [10, 11]:
        return 7
    return 7


def render_chat():
    """
    UX 원칙
    1) 일반 질문은 내용만큼만 표시해서 큰 빈 네모가 생기지 않는다.
    2) 꼬리질문 단계에서는 '앞 질문 + 내 선택'만 작은 스크롤 영역에 남긴다.
    3) 실제 꼬리질문은 그 아래에 바로 표시해서 흐름이 끊기지 않는다.
    4) 완료된 이전 상황들은 '이전 대화 보기'에 접어둔다.
    """
    messages = st.session_state.messages
    if not messages:
        return

    # 가장 최근의 '### 상황' 메시지를 현재 상황 시작점으로 사용
    scenario_indices = [
        i for i, msg in enumerate(messages)
        if msg["role"] == "assistant" and "### 상황" in msg["content"]
    ]

    if scenario_indices:
        current_start = scenario_indices[-1]
        previous = messages[:current_start]
        current_thread = messages[current_start:]
    else:
        previous = []
        current_thread = messages

    if previous:
        with st.expander("이전 대화 보기", expanded=False):
            for msg in previous:
                avatar = "🤖" if msg["role"] == "assistant" else "🙂"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

    # 꼬리질문이 나타나는 단계
    followup_stages = {3, 5, 8, 11}
    is_followup = st.session_state.stage in followup_stages and len(current_thread) >= 2

    if is_followup:
        # 마지막 assistant 메시지가 현재 꼬리질문.
        # 그 이전의 질문/사용자 선택은 작은 스크롤 문맥창에 유지한다.
        context_messages = current_thread[:-1]
        followup_message = current_thread[-1]

        if context_messages:
            st.caption("질문 맥락")
            with st.container(height=175, border=True):
                for msg in context_messages:
                    avatar = "🤖" if msg["role"] == "assistant" else "🙂"
                    with st.chat_message(msg["role"], avatar=avatar):
                        st.markdown(msg["content"])

        avatar = "🤖" if followup_message["role"] == "assistant" else "🙂"
        with st.chat_message(followup_message["role"], avatar=avatar):
            st.markdown(followup_message["content"])

    else:
        # 일반 질문은 고정 height 없이 자동 높이
        with st.container(border=True):
            for msg in current_thread:
                avatar = "🤖" if msg["role"] == "assistant" else "🙂"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])


def free_text_form(form_key, placeholder, button_label="답변 보내기", height=95):
    """
    화면 맨 아래에 고정되는 chat_input 대신
    현재 질문 바로 아래에 입력창을 배치한다.
    """
    with st.form(form_key, clear_on_submit=False):
        value = st.text_area(
            "답변",
            placeholder=placeholder,
            height=height,
            label_visibility="collapsed",
            key=f"{form_key}_text",
        )
        submitted = st.form_submit_button(button_label, use_container_width=True)

    if submitted:
        cleaned = value.strip()
        if not cleaned:
            st.warning("답변을 입력해주세요.")
            return None
        return cleaned

    return None


def reset_all():
    keys = [
        "stage",
        "messages",
        "answers",
        "scores",
        "option_orders",
        "result_ready",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# =========================================================
# 4. 상단
# =========================================================
if st.session_state.stage == 0:
    n = 0
    progress = 0.0
    status_left = "시작 전"
    status_right = "약 5~8분"
elif st.session_state.stage < 12:
    n = scenario_number(st.session_state.stage)
    progress = n / 7
    status_left = f"상황 {n} / 7"
    status_right = f"{int(progress * 100)}% 진행"
else:
    n = 7
    progress = 1.0
    status_left = "진단 완료"
    status_right = "100%"

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">AI LITERACY CHECK</div>
        <div class="app-title">AI 활용 사전진단</div>
        <div class="app-subtitle">짧은 상황을 해결하며 나의 AI 활용 방식을 확인해보세요.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="progress-row"><span>{status_left}</span><span>{status_right}</span></div>',
    unsafe_allow_html=True,
)
st.progress(progress)

render_chat()

# =========================================================
# 5. 단계별 진단
# =========================================================

# ---------------------------------------------------------
# Stage 0: 시작
# ---------------------------------------------------------
if st.session_state.stage == 0:
    st.markdown(
        """
        <div class="mission-card">
        <b>진단 방식</b><br>
        • 몇 가지 실제 사용 상황이 차례로 제시됩니다.<br>
        • 일부는 선택형, 일부는 짧은 자유응답입니다.<br>
        • 중간에는 점수나 정답을 보여주지 않습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("진단 시작하기 →", use_container_width=True):
        add_message("user", "진단 시작하기")
        add_message(
            "assistant",
            (
                "### 상황 1\n"
                "교수님이 **자유주제로 5분 발표**를 준비하라고 했습니다. 아직 주제를 정하지 못했습니다.\n\n"
                "**AI를 사용한다면 가장 먼저 무엇을 하시겠어요?**"
            ),
        )
        set_stage(1)

# ---------------------------------------------------------
# Stage 1: 인간의 주도권
# ---------------------------------------------------------
elif st.session_state.stage == 1:
    options = [
        ("요즘 발표하기 좋은 주제를 몇 개 추천해달라고 한다.", 1.0),
        ("내가 관심 있는 분야를 먼저 정하고, 그 안에서 발표 주제를 같이 찾아본다.", 2.0),
        ("과제 조건을 알려주고 가장 높은 점수를 받을 만한 주제를 하나 골라달라고 한다.", 0.5),
        ("다른 학생들이 많이 선택하는 발표 주제가 무엇인지 물어본다.", 1.0),
    ]

    ordered = shuffled_once("agency", options)
    for idx, (label, score) in enumerate(ordered):
        if st.button(label, key=f"agency_{idx}", use_container_width=True):
            save_choice("agency_choice", label, "agency", score)
            add_message(
                "assistant",
                (
                    "### 상황 2\n"
                    "발표를 준비하던 중 AI가 이런 정보를 알려줬습니다.\n\n"
                    "> **“2025년 조사에 따르면 대학생의 82.4%가 생성형 AI를 매일 사용합니다. "
                    "이 조사는 UNESCO가 실시했습니다.”**\n\n"
                    "발표 내용에 잘 맞아 보입니다. **다음으로 무엇을 하시겠어요?**"
                ),
            )
            set_stage(2)

# ---------------------------------------------------------
# Stage 2: 인간의 책임 - 행동 선택
# ---------------------------------------------------------
elif st.session_state.stage == 2:
    options = [
        ("발표자료에 우선 넣고, 시간이 되면 나중에 확인한다.", 0.0),
        ("AI에게 해당 조사의 링크나 출처를 요청한다.", 1.0),
        ("UNESCO 사이트나 원자료를 직접 찾아 조사와 수치를 확인한다.", 1.5),
        ("다른 AI에게 같은 내용을 물어보고 답이 같은지 비교한다.", 0.75),
    ]

    ordered = shuffled_once("responsibility", options)
    for idx, (label, score) in enumerate(ordered):
        if st.button(label, key=f"resp_{idx}", use_container_width=True):
            save_choice("responsibility_choice", label)
            st.session_state.answers["responsibility_base"] = score
            add_message(
                "assistant",
                "좋아요. **확인한다면 어떤 점을 가장 확인하고 싶은지** 짧게 적어주세요.",
            )
            set_stage(3)

# ---------------------------------------------------------
# Stage 3: 인간의 책임 - 이유
# ---------------------------------------------------------
elif st.session_state.stage == 3:
    text = free_text_form("responsibility_followup", "예: 실제 조사인지, 수치가 맞는지, 원출처가 무엇인지...")

    if text:
        add_message("user", text)
        st.session_state.answers["responsibility_reason"] = text

        base = float(st.session_state.answers.get("responsibility_base", 0))
        bonus = score_responsibility_reason(text)
        st.session_state.scores["responsibility"] = min(2.0, base + bonus)

        add_message(
            "assistant",
            (
                "### 상황 3\n"
                "한 회사가 AI로 신입사원 지원서를 자동 평가했습니다.\n\n"
                "결과를 확인해보니 **특정 대학 출신 지원자들이 계속 높은 점수**를 받고 있었습니다.\n"
                '담당자는 “AI가 일관된 기준으로 평가하기 때문에 사람보다 공정하다”고 말합니다.\n\n'
                "**이 상황에서 가장 먼저 확인하고 싶은 것은 무엇인가요?**"
            ),
        )
        set_stage(4)

# ---------------------------------------------------------
# Stage 4: 윤리적 관점 - 행동 선택
# ---------------------------------------------------------
elif st.session_state.stage == 4:
    options = [
        ("AI의 평가 정확도가 몇 %인지 확인한다.", 0.5),
        ("사람이 직접 평가했을 때보다 시간이 얼마나 단축됐는지 확인한다.", 0.0),
        ("AI가 어떤 데이터와 기준을 바탕으로 지원자를 평가했는지 확인한다.", 1.5),
        ("AI 평가를 도입한 뒤 최종 합격률이 얼마나 변했는지 확인한다.", 0.5),
    ]

    ordered = shuffled_once("ethics", options)
    for idx, (label, score) in enumerate(ordered):
        if st.button(label, key=f"ethics_{idx}", use_container_width=True):
            save_choice("ethics_choice", label)
            st.session_state.answers["ethics_base"] = score
            add_message(
                "assistant",
                "그 자료나 기준을 확인해서 **어떤 문제가 있는지 보고 싶은가요?** 짧게 적어주세요.",
            )
            set_stage(5)

# ---------------------------------------------------------
# Stage 5: 윤리적 관점 - 이유
# ---------------------------------------------------------
elif st.session_state.stage == 5:
    text = free_text_form("ethics_followup", "예: 특정 집단에 불리한 기준이 들어갔는지 등")

    if text:
        add_message("user", text)
        st.session_state.answers["ethics_reason"] = text

        base = float(st.session_state.answers.get("ethics_base", 0))
        bonus = score_ethics_reason(text)
        st.session_state.scores["ethics"] = min(2.0, base + bonus)

        add_message(
            "assistant",
            (
                "### 상황 4\n"
                "팀원 인터뷰 내용을 AI로 요약하려고 합니다. 원본에는 아래 정보가 포함되어 있습니다.\n\n"
                "```text\n"
                "김민수 / 경제학과 / 010-1234-5678\n"
                "“AI를 과제를 정리할 때 자주 사용한다.”\n\n"
                "박지영 / 컴퓨터공학과 / jihyeong@email.com\n"
                "“코딩할 때 주로 사용한다.”\n"
                "```\n\n"
                "**AI에게 전달하기 전에 제거하거나 가리고 싶은 항목을 모두 선택해주세요.**"
            ),
        )
        set_stage(6)

# ---------------------------------------------------------
# Stage 6: 안전하고 책임 있는 사용
# ---------------------------------------------------------
elif st.session_state.stage == 6:
    selected = st.multiselect(
        "제거하거나 가릴 항목",
        ["이름", "학과", "전화번호", "이메일", "인터뷰 내용", "수정 없이 사용"],
        placeholder="여러 개 선택할 수 있어요.",
    )

    if st.button("이 선택으로 진행하기", use_container_width=True):
        if not selected:
            st.warning("최소 한 가지를 선택해주세요.")
        else:
            st.session_state.answers["safety_selected"] = selected
            add_message("user", "제거/가림: " + ", ".join(selected))

            if "수정 없이 사용" in selected:
                score = 0.0
            else:
                sensitive = {"이름", "전화번호", "이메일"}
                removed_sensitive = len(sensitive.intersection(set(selected)))

                if removed_sensitive == 3:
                    score = 2.0
                elif removed_sensitive == 2:
                    score = 1.5
                elif removed_sensitive == 1:
                    score = 0.75
                else:
                    score = 0.25

                # 인터뷰 내용까지 전부 지우는 경우는 목적에 필요한 데이터까지 제거한 것이므로
                # 안전 인식은 있으나 활용 판단은 다소 과도한 것으로 본다.
                if "인터뷰 내용" in selected:
                    score = max(0.0, score - 0.25)

            st.session_state.scores["safety"] = score

            add_message(
                "assistant",
                (
                    "### 상황 5\n"
                    "AI가 다음과 같이 답했습니다.\n\n"
                    "> **“노벨상은 1901년부터 수학·물리학·화학·생리의학·문학·평화의 "
                    "6개 분야에서 수여되었습니다.”**\n\n"
                    "이 설명을 받은 뒤 **가장 가까운 생각**은 무엇인가요?"
                ),
            )
            set_stage(7)

# ---------------------------------------------------------
# Stage 7: AI의 기초 - 행동 선택
# ---------------------------------------------------------
elif st.session_state.stage == 7:
    options = [
        ("구체적인 연도와 분야까지 제시했으므로 신뢰할 수 있다고 생각한다.", 0.0),
        ("자연스럽게 설명했지만 사실관계는 따로 확인할 수 있다고 생각한다.", 1.25),
        ("유명한 주제이므로 AI도 정확히 알고 있을 가능성이 높다고 생각한다.", 0.5),
        ("표현을 조금 더 자세하게 만들어달라고 요청한다.", 0.25),
    ]

    ordered = shuffled_once("ai_basics", options)
    for idx, (label, score) in enumerate(ordered):
        if st.button(label, key=f"basics_{idx}", use_container_width=True):
            save_choice("ai_basics_choice", label)
            st.session_state.answers["ai_basics_base"] = score
            add_message(
                "assistant",
                "혹시 이 답변에서 **확인하고 싶은 부분이나 이상하다고 느껴지는 부분**이 있다면 적어주세요.",
            )
            set_stage(8)

# ---------------------------------------------------------
# Stage 8: AI의 기초 - 오류 탐지
# ---------------------------------------------------------
elif st.session_state.stage == 8:
    text = free_text_form("basics_followup", "없다면 '없음'이라고 입력해도 괜찮아요.")

    if text:
        add_message("user", text)
        st.session_state.answers["ai_basics_reason"] = text

        base = float(st.session_state.answers.get("ai_basics_base", 0))
        bonus = score_ai_basics_free(text)
        st.session_state.scores["ai_basics"] = min(2.0, base + bonus)

        add_message(
            "assistant",
            (
                "### 상황 6 · 실제로 AI에게 요청해보기\n"
                "대학 수업에서 **‘생성형 AI의 장점과 한계’를 주제로 5분 발표**를 해야 합니다.\n\n"
                "AI에게 도움을 요청한다면, **평소처럼 실제로 입력할 문장**을 작성해주세요."
            ),
        )
        set_stage(9)

# ---------------------------------------------------------
# Stage 9: 활용 능력 - 첫 프롬프트
# ---------------------------------------------------------
elif st.session_state.stage == 9:
    text = free_text_form("initial_prompt_form", "AI에게 실제로 요청하듯 작성해주세요.", "프롬프트 보내기", height=120)

    if text:
        add_message("user", text)
        st.session_state.answers["initial_prompt"] = text
        st.session_state.answers["initial_prompt_score"] = score_initial_prompt(text)

        # 일부러 '틀리진 않지만 일반적인 답변'을 보여준다.
        # 상황 7 안에 직전 AI 답변을 함께 넣어서, 사용자가 다시 찾아볼 필요가 없게 한다.
        add_message(
            "assistant",
            (
                "### 상황 7\n"
                "AI가 방금 이렇게 답했습니다.\n\n"
                "> 생성형 AI의 장점은 **업무 효율 향상, 정보 접근성 향상, 창의적인 아이디어 제공**입니다.  \n"
                "> 반면 한계로는 **잘못된 정보 생성, 개인정보 문제, 지나친 의존**이 있습니다.  \n"
                "> 발표에서는 이러한 장점과 한계를 균형 있게 설명하면 좋습니다.\n\n"
                "이 답변을 실제 발표 준비에 사용한다고 생각해보세요.\n\n"
                "**이대로 사용하시겠어요, 아니면 AI에게 한 번 더 요청하시겠어요?**"
            ),
        )
        set_stage(10)

# ---------------------------------------------------------
# Stage 10: 활용 능력 - 수정 여부
# ---------------------------------------------------------
elif st.session_state.stage == 10:
    c1, c2 = st.columns(2)

    with c1:
        if st.button("이대로 사용하기", use_container_width=True):
            label = "이대로 사용하기"
            add_message("user", label)
            st.session_state.answers["revision_decision"] = "use_as_is"

            first = float(st.session_state.answers.get("initial_prompt_score", 0))
            st.session_state.scores["utilization"] = min(2.0, first)

            add_message(
                "assistant",
                "진단이 끝났어요. 지금까지의 사용 방식을 바탕으로 결과를 정리해볼게요.",
            )
            set_stage(12)

    with c2:
        if st.button("한 번 더 요청하기", use_container_width=True):
            label = "한 번 더 요청하기"
            add_message("user", label)
            st.session_state.answers["revision_decision"] = "revise"
            add_message(
                "assistant",
                "좋아요. **어떤 점을 바꾸고 싶은지 AI에게 직접 수정 요청**을 해보세요.",
            )
            set_stage(11)

# ---------------------------------------------------------
# Stage 11: 활용 능력 - 수정 프롬프트
# ---------------------------------------------------------
elif st.session_state.stage == 11:
    text = free_text_form("revision_prompt_form", "예: 부족했던 점 + 원하는 조건을 함께 적어보세요.", "수정 요청 보내기", height=110)

    if text:
        add_message("user", text)
        st.session_state.answers["revision_prompt"] = text

        first = float(st.session_state.answers.get("initial_prompt_score", 0))
        revision = score_revision_prompt(text)
        st.session_state.answers["revision_prompt_score"] = revision
        st.session_state.scores["utilization"] = min(2.0, first + revision)

        add_message(
            "assistant",
            "진단이 끝났어요. 지금까지의 사용 방식을 바탕으로 결과를 정리해볼게요.",
        )
        set_stage(12)

# ---------------------------------------------------------
# Stage 12: 결과
# ---------------------------------------------------------
elif st.session_state.stage == 12:
    level_num, level_name, total = get_level(st.session_state.scores)

    level_desc = {
        1: "AI 활용에 필요한 기본 개념과 사용 원칙을 익혀가는 단계입니다.",
        2: "AI의 역할과 한계를 이해하고, 책임 있는 사용 원칙을 인식하고 있는 단계입니다.",
        3: "이해한 원칙을 실제 AI 사용 상황에 비교적 잘 적용할 수 있는 단계입니다.",
        4: "목적·책임·윤리·안전·AI 이해·활용을 전반적으로 고려하며 주도적으로 AI를 활용하는 단계입니다.",
    }

    st.markdown(
        f"""
        <div class="score-card">
            <div class="result-title">Level {level_num} · {level_name}</div>
            <div>{level_desc[level_num]}</div>
            <br>
            <b>총 역량 점수: {total:.2f} / 12</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 한눈에 보는 6개 역량")

    domain_items = list(DOMAINS.items())
    for row_start in range(0, 6, 3):
        cols = st.columns(3)
        for offset, (key, label) in enumerate(domain_items[row_start:row_start + 3]):
            score = float(st.session_state.scores[key])
            with cols[offset]:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.markdown(f'<div class="score-number">{score:.2f}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="score-label">2점 만점</div>', unsafe_allow_html=True)
                    st.progress(max(0.0, min(1.0, score / 2)))

    # 강점과 우선 개선 영역
    sorted_scores = sorted(st.session_state.scores.items(), key=lambda x: x[1])
    weakest = sorted_scores[:2]
    strongest = sorted_scores[-2:][::-1]

    left, right = st.columns(2)

    with left:
        st.markdown("### 강점")
        for key, score in strongest:
            st.success(f"**{DOMAINS[key]}**\n\n현재 진단에서 상대적으로 강하게 나타났어요.")

    with right:
        st.markdown("### 우선 연습")
        for key, score in weakest:
            st.info(f"**{DOMAINS[key]}**\n\n{DOMAIN_TIPS[key]}")

    with st.expander("내 응답 다시 보기"):
        for answer_key, answer_value in st.session_state.answers.items():
            if answer_key.endswith("_base") or answer_key.endswith("_score"):
                continue
            st.write(f"**{answer_key}**")
            st.write(answer_value)

    st.caption(
        "현재 버전은 사전진단 프로토타입입니다. 자유응답 일부는 규칙 기반으로 평가하며, "
        "추후 AI 평가와 사람 검토를 결합해 채점 기준을 정교화할 수 있습니다."
    )

    if st.button("처음부터 다시 진단하기", use_container_width=True):
        reset_all()

