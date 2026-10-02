import os
from google import genai
from google.genai import types

from prompt_builder import JUDGE_SYSTEM_PROMPT, build_fewshot_prompt
from schemas import EvaluationResult

class GeminiProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        model = model or os.getenv("GEMINI_MODEL")

        if not api_key:
            raise ValueError("GEMINI_API_KEY가 필요합니다.")
        if not model:
            raise ValueError("GEMINI_MODEL을 지정해주세요.")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    def evaluate(self, question_id: str, answer: str) -> EvaluationResult:
        prompt = build_fewshot_prompt(question_id, answer)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                # 중요:
                # response_schema를 넣지 않는다.
                # 기존 EvaluationResult의 evidence: Dict[...]가
                # JSON Schema에서 additionalProperties를 만들고,
                # 일부 Gemini Developer API 경로에서 이를 거부한다.
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")

        return EvaluationResult.model_validate_json(response.text)

