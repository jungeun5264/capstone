import os
import random
import time

from google import genai
from google.genai import types

from prompt_builder import JUDGE_SYSTEM_PROMPT, build_fewshot_prompt
from schemas import EvaluationResult


class GeminiProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_attempts: int = 4,
    ):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        model = model or os.getenv("GEMINI_MODEL")

        if not api_key:
            raise ValueError("GEMINI_API_KEY가 필요합니다.")
        if not model:
            raise ValueError("GEMINI_MODEL을 지정해주세요.")

        self.model = model
        self.max_attempts = max(1, max_attempts)
        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _is_temporary_server_error(exc: Exception) -> bool:
        """
        Gemini 서버의 일시적 과부하/Unavailable 계열만 재시도한다.
        인증, 잘못된 모델명, 잘못된 요청 형식 같은 오류는 즉시 사용자에게 전달한다.
        """
        text = str(exc).lower()

        retry_signals = (
            "503",
            "unavailable",
            "high demand",
            "temporarily unavailable",
            "service unavailable",
        )
        return any(signal in text for signal in retry_signals)

    def _generate(self, prompt: str):
        last_error = None

        for attempt in range(self.max_attempts):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=JUDGE_SYSTEM_PROMPT,
                        temperature=0.1,
                        response_mime_type="application/json",
                        # response_schema는 사용하지 않음:
                        # Dict 형태의 evidence가 additionalProperties를 만들 수 있어
                        # Gemini Developer API와 충돌할 수 있음.
                    ),
                )

            except Exception as exc:
                last_error = exc

                # 503 계열이 아니면 재시도하지 않고 원래 오류를 바로 보여준다.
                if not self._is_temporary_server_error(exc):
                    raise

                # 마지막 시도까지 실패한 경우
                if attempt == self.max_attempts - 1:
                    break

                # 1초 → 2초 → 4초 수준의 exponential backoff + 작은 jitter
                wait_seconds = (2 ** attempt) + random.uniform(0.0, 0.5)
                time.sleep(wait_seconds)

        raise RuntimeError(
            "현재 Gemini 서버 사용량이 많아 요청을 처리하지 못했습니다. "
            "잠시 후 다시 시도해주세요."
        ) from last_error

    def evaluate(self, question_id: str, answer: str) -> EvaluationResult:
        prompt = build_fewshot_prompt(question_id, answer)
        response = self._generate(prompt)

        if not response.text:
            raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")

        try:
            return EvaluationResult.model_validate_json(response.text)
        except Exception as exc:
            raise RuntimeError(
                "Gemini 응답을 평가 결과 형식으로 해석하지 못했습니다. "
                "같은 요청을 한 번 더 시도해주세요."
            ) from exc

