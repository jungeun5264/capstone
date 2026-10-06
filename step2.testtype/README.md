# AI Practice Lab v3

큐랩 화면을 복제하지 않고, `상황 선택 → Gemini 협업 → 3개의 파생 상황 → 최종안 작성 → 6축 분석` 흐름으로 다시 만든 테스트 버전입니다.

## 1) Streamlit Cloud에서 가장 빠르게 테스트

GitHub 저장소에 이 폴더의 파일을 올립니다. `app.py`가 이 폴더 안에 있다면 Streamlit Cloud의 Main file path는 예를 들어 다음처럼 지정합니다.

```text
ai_training_lab_v3/app.py
```

Streamlit Cloud의 **App settings → Secrets**에 아래를 넣습니다.

```toml
GEMINI_API_KEY = "본인의_Gemini_API_Key"
GEMINI_MODEL = "gemini-3.8-flash"
```

`.env`나 `.streamlit/secrets.toml`을 GitHub에 업로드하지 마세요.

## 2) 로컬 실행

```bash
pip install -r requirements.txt
```

`.env.example`을 `.env`로 복사한 뒤 API Key를 입력합니다.

```env
GEMINI_API_KEY=본인의_API_Key
GEMINI_MODEL=gemini-3.8-flash
```

그 다음:

```bash
streamlit run app.py
```

## 3) 이번 버전에서 달라진 점

- 큐랩의 카드/레이아웃을 직접 따라가지 않는 별도 디자인
- `훈련 시작` 시 빈 화면이 아니라 Gemini가 실제 첫 메시지와 3개의 파생 상황을 준비
- `st.chat_input` 대신 일반 입력창+버튼을 사용해 컬럼 내부에서 채팅 입력이 사라지는 문제를 피함
- 파생 상황은 Gemini가 매 도전 새로 생성
- 사용자가 `새 상황 열기` 버튼으로 다음 변수를 단계적으로 받음
- 채팅 Gemini와 평가 Gemini 역할 분리
- 결과 화면에서 6개 역량 레이더 차트 및 이전 도전과 비교
- API Key가 없으면 `UI 데모` 모드로 화면만 테스트 가능

## 4) 테스트 순서

1. 사이드바에서 `Gemini` 선택 및 연결 표시 확인
2. 부산 여행 상황 선택
3. `훈련 시작`
4. Gemini에게 첫 요청 전송
5. `새 상황 열기 (1/3)`을 눌러 파생 상황 확인
6. 기존 계획을 수정하며 2, 3번째 상황까지 진행
7. 오른쪽 `나의 최종안` 작성
8. `분석하고 결과 보기`
9. 레이더 차트와 피드백 확인
10. `다른 조건으로 다시 도전`하여 Gemini가 새 파생 상황을 만드는지 확인

## 5) 파일 구조

```text
ai_training_lab_v3/
├─ app.py
├─ missions.py
├─ gemini_service.py
├─ scoring.py
├─ demo_mode.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ .streamlit/
   └─ config.toml
```
