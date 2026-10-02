from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dataset import load_framework, load_questions
from judge import get_provider
from schemas import EvaluateRequest

app = FastAPI(
    title="AI Competency Coach API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 실제 배포 시 친구의 프론트엔드 주소로 제한
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/framework")
def framework():
    return load_framework()

@app.get("/questions")
def questions():
    return load_questions()

@app.get("/questions/{question_id}")
def question(question_id: str):
    for q in load_questions():
        if q["question_id"] == question_id:
            return q
    raise HTTPException(status_code=404, detail="question_id not found")

@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    try:
        result = get_provider().evaluate(req.question_id, req.answer)
        return result.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"evaluation failed: {type(e).__name__}"
        ) from e
