import streamlit as st

st.set_page_config(
    page_title="AI 활용 사전진단",
    page_icon="🤖",
    layout="centered"
)

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
    .block-container {
        max-width: 820px;
        padding-top: 2rem;
    }

    .diagnosis-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .diagnosis-subtitle {
        color: #777;
        margin-bottom: 20px;
    }

    div.stButton > button {
        width: 100%;
        text-align: left;
        border-radius: 12px;
        padding: 12px 16px;
    }

    .result-box {
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #dddddd;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 초기 상태
# -----------------------------
if "stage" not in st.session_state:
    st.session_state.stage = 0

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content":
            "안녕하세요! 👋 저는 여러분이 AI를 얼마나 효과적으로 활용하고 있는지 "
            "알아보는 AI 코치예요.\n\n"
            "시험처럼 정답을 맞히는 과정은 아니니 편하게 답해주세요."
        },
        {
            "role": "assistant",
            "content":
            "먼저 간단하게 시작해볼게요.\n\n"
            "**평소 ChatGPT나 Gemini 같은 생성형 AI를 얼마나 자주 사용하나요?**"
        }
    ]

if "profile" not in st.session_state:
    st.session_state.profile = {}

if "scores" not in st.session_state:
    st.session_state.scores = {
        "목표 명확성": 0,
        "맥락 제공": 0,
        "출력 구조화": 0,
        "반복·수정": 0,
        "정보 검증": 0
    }


# -----------------------------
# 질문
# -----------------------------
questions = {

    1:
    """좋아요. 그럼 AI를 **가장 많이 사용하는 목적**은 무엇인가요?""",

    2:
    """
이번에는 실제 사용 상황을 하나 드릴게요.

📌 **상황**

> 대학 수업에서  
> **'생성형 AI의 장점과 단점을 조사해서 발표하라'**는 과제를 받았습니다.

AI에게 도움을 요청한다면 **실제로 어떻게 입력할 것 같은지** 아래에 적어주세요.

잘 쓰려고 일부러 고민하지 않아도 괜찮아요. 평소 스타일대로 작성해주세요.
""",

    3:
    """
좋습니다. 이번에는 AI가 답변을 해줬는데  
**내용이 너무 뻔하고 내가 원하는 방향과 다르다고 가정해볼게요.**

이때 보통 어떻게 하시겠어요?
""",

    4:
    """
이번에는 AI가 발표 자료에 사용할 만한  
**통계 수치와 논문 정보를 알려줬다고 가정해볼게요.**

이 정보를 사용할 때 어떻게 하시겠어요?
""",

    5:
    """
마지막 질문이에요!

AI에게 결과물을 받을 때 **출력 형태를 얼마나 구체적으로 지정하는 편인가요?**
"""
}


# -----------------------------
# 함수
# -----------------------------
def add_next_question():
    stage = st.session_state.stage

    if stage in questions:
        st.session_state.messages.append({
            "role": "assistant",
            "content": questions[stage]
        })


def next_stage(answer):
    st.session_state.messages.append({
        "role": "user",
        "content": answer
    })

    st.session_state.stage += 1

    if st.session_state.stage <= 5:
        add_next_question()
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content":
            "좋아요! 🎉 모든 질문이 끝났어요.\n\n"
            "답변을 바탕으로 현재 AI 활용 방식을 정리해볼게요."
        })

    st.rerun()


# -----------------------------
# 자유 프롬프트 간단 평가
# -----------------------------
def score_prompt(text):

    text_lower = text.lower()

    goal = 2
    context = 1
    structure = 1

    # 길이
    if len(text) >= 30:
        goal += 2
        context += 1

    if len(text) >= 70:
        context += 2
        structure += 1

    # 목적성
    goal_keywords = [
        "목적", "발표", "과제", "비교", "분석",
        "설명", "정리", "작성", "알려줘"
    ]

    if any(word in text_lower for word in goal_keywords):
        goal += 3

    # 맥락
    context_keywords = [
        "대학생", "학생", "수업", "발표",
        "교수", "청중", "전공", "배경",
        "주제", "상황"
    ]

    if any(word in text_lower for word in context_keywords):
        context += 3

    # 출력 방식
    structure_keywords = [
        "표", "목차", "단계", "bullet",
        "항목", "분량", "글자", "슬라이드",
        "예시", "형식", "순서"
    ]

    if any(word in text_lower for word in structure_keywords):
        structure += 4

    st.session_state.scores["목표 명확성"] = min(goal, 10)
    st.session_state.scores["맥락 제공"] = min(context, 10)
    st.session_state.scores["출력 구조화"] = min(structure, 10)


# -----------------------------
# 제목
# -----------------------------
st.markdown(
    '<div class="diagnosis-title">AI 활용 사전진단</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="diagnosis-subtitle">'
    '몇 번의 대화를 통해 나의 AI 활용 습관을 알아보세요.'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 진행도
# -----------------------------
progress = min(st.session_state.stage / 6, 1.0)

st.progress(progress)

if st.session_state.stage < 6:
    st.caption(f"진단 진행도 {st.session_state.stage + 1} / 6")


# -----------------------------
# 채팅 기록 출력
# -----------------------------
for message in st.session_state.messages:

    avatar = "🤖" if message["role"] == "assistant" else "🙂"

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):
        st.markdown(message["content"])


# =========================================================
# STEP 0
# AI 사용 빈도
# =========================================================
if st.session_state.stage == 0:

    options = [
        "거의 사용하지 않는다",
        "가끔 필요할 때 사용한다",
        "일주일에 여러 번 사용한다",
        "거의 매일 사용한다"
    ]

    for option in options:

        if st.button(
            option,
            key=f"experience_{option}"
        ):
            st.session_state.profile["experience"] = option
            next_stage(option)


# =========================================================
# STEP 1
# 주요 사용 목적
# =========================================================
elif st.session_state.stage == 1:

    options = [
        "📚 공부·과제",
        "✍️ 글쓰기·문서 작성",
        "💻 코딩·데이터 분석",
        "💡 아이디어·기획",
        "🔍 정보 검색·정리",
        "🎨 콘텐츠 제작"
    ]

    for option in options:

        if st.button(
            option,
            key=f"purpose_{option}"
        ):
            st.session_state.profile["purpose"] = option
            next_stage(option)


# =========================================================
# STEP 2
# 실제 프롬프트 작성
# =========================================================
elif st.session_state.stage == 2:

    prompt_answer = st.chat_input(
        "평소 AI에게 말하듯 입력해주세요."
    )

    if prompt_answer:

        st.session_state.profile["test_prompt"] = prompt_answer

        score_prompt(prompt_answer)

        next_stage(prompt_answer)


# =========================================================
# STEP 3
# 반복 수정 능력
# =========================================================
elif st.session_state.stage == 3:

    options = {
        "그냥 다시 생성해본다": 2,
        "예: '좀 더 자세히 해줘'라고 요청한다": 4,
        "마음에 들지 않는 부분을 구체적으로 알려준다": 8,
        "문제점을 설명하고 예시·조건을 추가해서 다시 요청한다": 10
    }

    for option, score in options.items():

        if st.button(
            option,
            key=f"iteration_{score}"
        ):
            st.session_state.scores["반복·수정"] = score
            next_stage(option)


# =========================================================
# STEP 4
# 정보 검증
# =========================================================
elif st.session_state.stage == 4:

    options = {
        "AI가 알려준 내용을 그대로 사용한다": 1,
        "틀린 것 같을 때만 검색해본다": 4,
        "AI에게 출처를 요청하고 확인한다": 7,
        "논문·공식 자료 등 원출처를 직접 확인한다": 10
    }

    for option, score in options.items():

        if st.button(
            option,
            key=f"verification_{score}"
        ):
            st.session_state.scores["정보 검증"] = score
            next_stage(option)


# =========================================================
# STEP 5
# 출력 구조화
# =========================================================
elif st.session_state.stage == 5:

    options = {
        "거의 지정하지 않는다": 2,
        "짧게 / 자세히 정도만 지정한다": 4,
        "표·목록·문단 등 형식을 지정한다": 7,
        "형식·분량·대상·톤·예시까지 구체적으로 지정한다": 10
    }

    for option, score in options.items():

        if st.button(
            option,
            key=f"format_{score}"
        ):
            # 기존 프롬프트 기반 구조화 점수와 비교하여
            # 더 높은 점수를 사용
            st.session_state.scores["출력 구조화"] = max(
                st.session_state.scores["출력 구조화"],
                score
            )

            next_stage(option)


# =========================================================
# 결과 화면
# =========================================================
elif st.session_state.stage >= 6:

    scores = st.session_state.scores

    average_score = sum(scores.values()) / len(scores)

    if average_score >= 8:
        level = "🚀 Level 4 · 전략적 활용"
        explanation = "AI에게 단순히 질문하는 것을 넘어 목적에 맞게 통제하고 검증하는 능력이 높아요."

    elif average_score >= 6:
        level = "✨ Level 3 · 실전 활용"
        explanation = "AI를 적극적으로 활용하고 있지만 몇 가지 요소를 보완하면 결과의 품질을 크게 높일 수 있어요."

    elif average_score >= 4:
        level = "🌱 Level 2 · 기본 활용"
        explanation = "AI 사용에는 익숙하지만 질문을 구조화하고 결과를 검증하는 습관을 조금 더 키워볼 수 있어요."

    else:
        level = "🐣 Level 1 · 탐색 단계"
        explanation = "AI의 기본적인 활용법부터 차근차근 익히면 빠르게 실력이 올라갈 수 있어요."

    st.markdown("## 🧠 나의 AI 활용 진단")

    st.markdown(f"""
    <div class="result-box">

    ### {level}

    {explanation}

    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 세부 역량")

    for name, score in scores.items():

        st.write(f"**{name} · {score}/10**")

        st.progress(score / 10)

    # 가장 낮은 두 영역
    weak_areas = sorted(
        scores.items(),
        key=lambda x: x[1]
    )[:2]

    recommendations = {

        "목표 명확성":
        "AI에게 질문하기 전에 '내가 최종적으로 무엇을 얻고 싶은가?'를 한 문장으로 정리해보세요.",

        "맥락 제공":
        "대상, 상황, 사용 목적과 같은 배경 정보를 함께 알려주면 AI의 답변이 훨씬 정확해집니다.",

        "출력 구조화":
        "표, 목록, 분량, 문체처럼 원하는 결과물의 형태를 구체적으로 지정해보세요.",

        "반복·수정":
        "첫 번째 답변을 최종 결과라고 생각하지 말고, 부족한 부분을 알려주며 AI와 반복해서 개선해보세요.",

        "정보 검증":
        "숫자, 논문, 법률, 최신 정보처럼 중요한 내용은 반드시 원출처를 확인하는 습관을 가져보세요."
    }

    st.markdown("### 🎯 먼저 연습하면 좋은 부분")

    for area, score in weak_areas:
        st.info(
            f"**{area}**\n\n"
            f"{recommendations[area]}"
        )

    if st.button(
        "🔄 처음부터 다시 진단하기",
        use_container_width=True
    ):
        for key in [
            "stage",
            "messages",
            "profile",
            "scores"
        ]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()
