# 디딤돌 v9 — 친구 디자인 원본 유지 + GPT Luna 전용 훈련

## 친구 파일 4개 보호
`index.html`, `diagnosis.html`, `style.css`, `diagnosis.css` **네 파일은 전달받은 원본과 바이트가 동일**합니다.
`FRIEND_ORIGINALS_SHA256.txt`에 해시를 기록했습니다.

- 홈/진단 안내 페이지는 별도로 다시 그린 것이 아니라 **친구의 HTML과 CSS를 직접 렌더링**합니다.
- `friend_pages.py`가 화면에 보여줄 때만 링크를 `?view=...` 로 변환합니다. Chrome에서 새 탭이 생기지 않도록 `target="_self"`를 적용합니다. 원본 파일은 수정하지 않습니다.
- 친구의 진단 안내에는 구형 문항 수(12문항/영역별 4문항)가 적혀 있어 **표시할 때만** 실제 `test.py`의 7개 상황/6개 역량으로 바꿉니다. 원본 `diagnosis.html`의 문구는 그대로입니다.

## 실제 기능
- `test.py`: 사용자가 전달한 `test (1).py` 원본 진단 로직/점수(7개 상황, 6영역 × 2점) 유지. 통합 앱에 맞게 `render()` 함수화.
- `training.py`: 최신 `app (8).py` 문제 훈련 로직 기반. **GPT Luna API 전용**. 데모/Luna 선택 라디오 제거.
- `training.css`: 카드형 문제목록 및 훈련 영역 디자인 (친구 원본 CSS와 분리).
- `luna_service.py`: OpenAI Responses API 연동.
- `missions.py`, `scoring.py`: 상황/역량점수 산출.
- 홈 → 사전진단 안내 → 진단 진행 → 문제훈련. 페이지 이동 시 새 탭을 만들지 않습니다.

## Windows 실행
1. 압축을 풀고 `app.py`와 `requirements.txt`가 보이는 폴더로 이동합니다.
2. `START_WINDOWS.bat`을 더블 클릭합니다. 또는 VS Code 터미널에서 다음 명령어를 실행합니다.
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
3. `http://localhost:8501` 접속. 기존 서버는 `Ctrl+C`로 종료하고 **하나만 실행**하세요.

## API 설정 (필수)
`.streamlit/secrets.toml.example`을 복사해 `.streamlit/secrets.toml`이라는 이름으로 저장합니다.
```toml
OPENAI_API_KEY = "sk-실제_API_키"
OPENAI_MODEL = "gpt-6-luna"
```
배포할 때는 Streamlit Cloud 앱 설정의 Secrets에 등록합니다. **절대로 GitHub에 키를 올리지 마세요.**
`secrets.toml`은 `.gitignore`에 있습니다. ChatGPT 구독과 OpenAI API 요금은 별도입니다.

## 확인사항
- 진단 화면은 원래 Python `test.py`의 Streamlit 구성입니다. 친구의 `diagnosis.html`은 진단 **안내 화면**으로 표시됩니다.
- 친구 원본 HTML의 회원가입/Prompt Coach/마이페이지는 아직 작동하는 코드가 없어 안내 페이지로 연결합니다. 기능이 완료되었다고 표시하지 않습니다.
- 실제 로그인 및 DB 영구 저장은 아직 구현하지 않았습니다.
- HTML 링크는 동일 탭의 `?view=` 주소로 이동합니다. 이는 Streamlit 세션을 재연결할 수 있으므로 장시간 진행 중인 훈련에서 홈을 이동하는 경우 세션 보존을 보장하지 않습니다. 진단/훈련 **내부**는 Streamlit 버튼으로 이동합니다.
- 실제 GPT Luna API 키 없이 API 호출 테스트는 할 수 없으며, 로그인/사용자별 기록 저장도 다음 단계에서 추가해야 합니다.
