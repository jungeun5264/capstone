# AI 역량 훈련 Lab v2

큐랩 형태를 참고해 만든 Streamlit 프로토타입입니다.

## 포함된 흐름

1. 훈련 라이브러리에서 여러 상황 중 선택
2. 과제 상세: 한 줄 요약 / 상황 / 수행 목표 / 제약 조건 / 시작 가이드
3. 실전 훈련: 왼쪽 Gemini 대화, 오른쪽 과제 확인 + 최종 결과물 작성
4. 대화가 진행될수록 파생 상황이 순차적으로 공개됨
5. 제출 시 대화 + 파생 상황 대응 + 최종 결과물을 함께 평가
6. 6개 AI 역량 육각형 결과
7. 재도전 시 동일 과제라도 다른 파생 상황 세트 사용
8. 1차/2차 점수 및 육각형 비교

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

처음에는 사이드바의 **토큰 없이 데모 모드**가 켜져 있습니다. 이 상태에서는 Gemini API를 호출하지 않습니다.

## 실제 Gemini 사용

`.env.example`을 복사해 `.env`로 만들고 API Key를 넣습니다.

```env
GEMINI_API_KEY=...
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EVAL_MODEL=gemini-2.5-flash
```

그 다음 앱 사이드바에서 `토큰 없이 데모 모드`를 끕니다.

Streamlit Cloud에서는 `.env`를 GitHub에 올리지 말고 App Settings → Secrets에 다음처럼 넣으세요.

```toml
GEMINI_API_KEY = "..."
```

## 파생 상황 공개 규칙

현재 프로토타입에서는 사용자 발화가 2회 누적될 때마다 새로운 상황이 하나씩 공개됩니다.
예: 2회 → 상황 1, 4회 → 상황 2, 6회 → 상황 3.

이 숫자는 `app.py`의 `maybe_reveal_event()`에서 쉽게 바꿀 수 있습니다.

## 사전진단 연결

현재는 사이드바의 샘플 점수를 초기 프로필로 사용합니다.
기존 사전진단 페이지와 합칠 때 `st.session_state.baseline`에 실제 6개 진단 점수를 넘기면 됩니다.
