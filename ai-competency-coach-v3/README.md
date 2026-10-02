# AI Competency Coach

사용자가 정리한 6개 AI 활용 역량을 상황형 문항으로 평가하는 백엔드 프로토타입입니다.

## 현재 데이터

- 6개 역량
- 역량당 3개 상황형 문항 = 18문항
- 문항당 0/1/2/3점 기준답안 = 72개
- 각 기준답안에 score + evidence 포함

## 현재 권장 학습 방식

바로 fine-tuning하지 않고 먼저 few-shot Judge로 사용합니다.

새 답변이 들어오면:
1. 해당 역량 정의
2. evidence
3. 0~3 rubric
4. 같은 문항의 0/1/2/3 기준답안
5. 같은 역량의 다른 상황 예시

를 AI에게 같이 보내 새 답변을 채점합니다.

이 역할은 `prompt_builder.py`가 담당합니다.

## 가장 먼저 할 일

`data/labeled_examples_review.csv`를 사람이 검토하세요.

현재 72개 예시는 초기 초안이며:
- 점수가 적절한지
- evidence가 맞는지
- 특정 표현에 과도하게 편향되지 않았는지

검토 후 `human_validated` 값을 TRUE로 바꾸는 것을 권장합니다.

## Gemini 없이 테스트

기본 모드는 mock입니다.

```bash
pip install -r requirements.txt
uvicorn api:app --reload
```

API 문서:
`http://127.0.0.1:8000/docs`

Streamlit:
```bash
streamlit run app.py
```

## Gemini 연결 후

환경변수:

```text
JUDGE_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=...
```

그 뒤 앱을 다시 실행하면 `GeminiProvider`가 rubric + examples를 이용해 평가합니다.

## API

POST `/evaluate`

```json
{
  "question_id": "H1-01",
  "answer": "AI에게 회사별 장단점을 비교하게 하고 제가 최종 결정하겠습니다."
}
```

응답:

```json
{
  "question_id": "H1-01",
  "competency_id": "HC_AGENCY",
  "score": 2,
  "evidence": {
    "goal_setting": "partial",
    "ai_role_setting": "clear",
    "human_final_decision": "clear"
  },
  "reason": "...",
  "feedback": "...",
  "next_step": "...",
  "confidence": 0.87
}
```

## fine-tuning 준비 파일 만들기

```bash
python export_training_data.py
```

`data/training_ready_messages.jsonl` 생성.

단, 실제 fine-tuning 전에 반드시 사람이 검수한 데이터만 사용하세요.
