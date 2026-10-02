# AI Prompt Coach API Contract

## POST /analyze

Request:

```json
{
  "prompt": "논문 요약해줘",
  "target_ai": "ChatGPT"
}
```

Response shape:

```json
{
  "intent": "사용자의 실제 목적",
  "task_type": "요약",
  "scores": {
    "goal": {"score": 12, "reason": "...", "improvement": "..."},
    "context": {"score": 5, "reason": "...", "improvement": "..."},
    "constraints": {"score": 5, "reason": "...", "improvement": "..."},
    "output": {"score": 5, "reason": "...", "improvement": "..."},
    "verification": {"score": 4, "reason": "...", "improvement": "..."}
  },
  "strengths": ["..."],
  "improvements": ["..."],
  "coach_questions": ["..."],
  "revised_prompt": "...",
  "learning_point": "...",
  "capability_focus": "Use",
  "capability_reason": "...",
  "total_score": 31
}
```

프론트엔드는 이 JSON만 알면 되며 Gemini 내부 구현을 알 필요가 없습니다.
