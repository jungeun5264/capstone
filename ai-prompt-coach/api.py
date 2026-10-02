import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prompt_coach import DEFAULT_MODEL, PromptCoach, to_api_payload

app = FastAPI(title="AI Prompt Coach API", version="0.1.0")

default_origins = "http://localhost:3000,http://localhost:5173"
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", default_origins).split(",") if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1)
    target_ai: str = "범용 AI"

def get_coach() -> PromptCoach:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return PromptCoach(api_key=api_key, model=model)

@app.get("/health")
def health():
    return {"status": "ok", "model": os.getenv("GEMINI_MODEL", DEFAULT_MODEL)}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        result = get_coach().analyze(request.prompt, request.target_ai)
        return to_api_payload(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt analysis failed: {type(e).__name__}") from e
