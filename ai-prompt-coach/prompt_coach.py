from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
from schemas import PromptAnalysis

DEFAULT_MODEL = "gemini-3.8-flash"

class PromptCoach:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 필요합니다.")
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def analyze(self, user_prompt: str, target_ai: str = "범용 AI") -> PromptAnalysis:
        user_prompt = (user_prompt or "").strip()
        if not user_prompt:
            raise ValueError("분석할 프롬프트를 입력해주세요.")

        request_text = (
            "[평가 대상 프롬프트]\n"
            f"{user_prompt}\n\n"
            "[사용자가 이 프롬프트를 사용할 AI]\n"
            f"{target_ai}\n\n"
            "[지시]\n"
            "위 프롬프트 자체를 평가하세요. 개선된 프롬프트를 기준으로 점수를 주지 마세요. "
            "다섯 평가 항목은 서로 독립적으로 판단하세요. "
            "target_ai의 특성이 실제로 중요한 경우에만 개선안에 반영하세요."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=request_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=PromptAnalysis,
            ),
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, PromptAnalysis):
            return parsed
        if parsed is not None:
            return PromptAnalysis.model_validate(parsed)
        if not response.text:
            raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
        return PromptAnalysis.model_validate_json(response.text)

def total_score(result: PromptAnalysis) -> int:
    s = result.scores
    return s.goal.score + s.context.score + s.constraints.score + s.output.score + s.verification.score

def to_api_payload(result: PromptAnalysis) -> dict:
    data = result.model_dump()
    data["total_score"] = total_score(result)
    return data
