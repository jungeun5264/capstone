import os
from providers.mock_provider import MockProvider

def get_provider():
    mode = os.getenv("JUDGE_PROVIDER", "mock").lower()

    if mode == "mock":
        return MockProvider()

    if mode == "gemini":
        from providers.gemini_provider import GeminiProvider
        return GeminiProvider()

    raise ValueError(f"Unsupported JUDGE_PROVIDER: {mode}")
