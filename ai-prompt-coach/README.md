# AI Prompt Coach

## 구조

```text
ai-prompt-coach/
├── app.py
├── api.py
├── prompt_coach.py
├── schemas.py
├── prompts.py
├── API_CONTRACT.md
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml.example
```

## 지금: Streamlit으로 기능 확인

GitHub에 repository를 만들고 위 파일들을 업로드합니다.

Streamlit Community Cloud에서:
1. Create app
2. GitHub repository 선택
3. Main file path: `app.py`
4. Advanced settings > Secrets에 아래 입력

```toml
GEMINI_API_KEY = "실제_API_KEY"
GEMINI_MODEL = "gemini-3.8-flash"
```

5. Deploy

실제 API Key는 GitHub에 올리지 마세요.

## 나중에 친구 UI와 연결

`api.py`를 별도 백엔드 서버에서 실행합니다.

macOS/Linux:
```bash
export GEMINI_API_KEY="실제_API_KEY"
uvicorn api:app --reload --port 8000
```

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="실제_API_KEY"
uvicorn api:app --reload --port 8000
```

프론트엔드는 `POST /analyze`에 다음처럼 요청하면 됩니다.

```json
{
  "prompt": "논문 요약해줘",
  "target_ai": "ChatGPT"
}
```

자세한 응답 형식은 `API_CONTRACT.md`를 참고하세요.
