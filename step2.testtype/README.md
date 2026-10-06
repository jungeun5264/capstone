# AI 역량 훈련 프로토타입

부산 2박 3일 여행 미션을 이용해 다음 흐름을 테스트하는 Streamlit 프로토타입입니다.

**미션 → AI 채팅 → 제출 → 6개 역량 평가 → 육각형 레이더 차트 → 재도전 비교**

## 1. 가장 빠른 테스트: 데모 모드

API 키 없이 UI와 전체 흐름을 확인할 수 있습니다.

```bash
pip install -r requirements.txt
streamlit run app.py
```

웹이 열리면 왼쪽 사이드바의 **토큰 없이 데모 모드**를 켠 상태로 사용하세요.

데모 모드의 평가는 실제 Gemini 평가가 아니라, 특정 행동 표현을 찾아 점수를 만드는 테스트용 로직입니다.

## 2. 실제 Gemini 연결

1. `.env.example`을 복사해 `.env` 파일을 만듭니다.
2. `GEMINI_API_KEY`에 본인의 Google AI Studio API 키를 입력합니다.
3. 웹 사이드바에서 **토큰 없이 데모 모드**를 끕니다.

```bash
streamlit run app.py
```

`.env` 예시:

```env
GEMINI_API_KEY=YOUR_KEY
GEMINI_CHAT_MODEL=gemini-3.8-flash
GEMINI_EVAL_MODEL=gemini-3.8-flash
```

프로젝트에서 기존 Gemini 모델을 쓰고 있다면 모델명만 바꾸면 됩니다.

## 3. 파일 역할

- `app.py`: Streamlit UI, 세션 상태, 레이더 차트, 재도전 흐름
- `gemini_service.py`: 실제 Gemini 채팅/평가 호출 및 평가 JSON schema
- `scoring.py`: 0~4점 세부 평가를 0~100으로 환산, 종합점수/성장량 계산
- `demo_mode.py`: API 토큰 없이 테스트하기 위한 모의 채팅/채점

## 4. 6개 역량

1. AI의 기초 이해
2. AI 활용 능력
3. 인간의 주도권
4. 인간의 책임
5. 윤리적 관점
6. 안전하고 책임 있는 사용

여행 미션에서는 앞의 4개를 중심으로 평가합니다. 윤리/안전은 관련 행동이 실제로 관찰된 경우에만 평가하고, 그렇지 않으면 `evaluated=false`로 처리합니다.

## 5. 사전진단 페이지와 연결할 때

현재 프로토타입은 사이드바에 사전진단 샘플 점수를 넣어두었습니다. 실제 서비스에서는 `DEFAULT_BASELINE` 대신 기존 사전진단 결과를 `st.session_state.baseline_profile`에 넣으면 됩니다.

예:

```python
st.session_state.baseline_profile = {
    "ai_basic": diagnosis["ai_basic"],
    "ai_usage": diagnosis["ai_usage"],
    "human_agency": diagnosis["human_agency"],
    "human_responsibility": diagnosis["human_responsibility"],
    "ethical_view": diagnosis["ethical_view"],
    "safe_use": diagnosis["safe_use"],
}
```

## 6. 다음 통합 포인트

현재는 같은 부산 미션의 재도전까지 구현되어 있습니다. 다음 단계에서 전이 미션(예: 동아리 워크숍)을 추가한 뒤, 전이 미션에서도 성과가 유지될 때 장기 프로필을 업데이트하는 구조로 확장하면 됩니다.
