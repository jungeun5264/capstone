# AI Practice Lab v4 — OpenAI Luna

기존 Gemini 버전을 OpenAI Luna API로 교체한 Streamlit 테스트 버전입니다.

## 1. 설치

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 2. Streamlit Cloud Secrets

Streamlit Cloud → **Manage app → Settings → Secrets**에 아래처럼 넣으세요.

```toml
OPENAI_API_KEY = "sk-발급받은_API_키"
OPENAI_MODEL = "gpt-6-luna"
```

API 키는 GitHub 코드나 `.env` 파일에 커밋하지 마세요.

## 3. GitHub / Streamlit Cloud

이 폴더를 GitHub에 올린 경우 Main file path는 예를 들어:

```text
ai_training_lab_v4_luna/app.py
```

로 지정합니다.

## 4. 이번 버전에서 Luna가 하는 일

- 훈련 시작 시 파생 상황 3개 생성
- 훈련 중 사용자와 실제 대화
- 제출 후 전체 대화 + 파생 상황 대응 + 최종 결과물을 분석
- 6가지 AI 역량을 0~4 행동 루브릭으로 평가

점수 환산과 레이더 차트는 Streamlit 코드가 처리합니다.

## 5. 모델 변경

기본 모델은 `gpt-6-luna`입니다. 특정 버전을 테스트하고 싶다면 Secrets의 `OPENAI_MODEL`만 바꾸면 됩니다.

예:

```toml
OPENAI_MODEL = "gpt-5.6-luna"
```
