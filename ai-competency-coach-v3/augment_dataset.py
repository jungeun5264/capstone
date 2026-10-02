import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Literal

from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EvidenceStatus = Literal["absent", "partial", "clear"]

class GeneratedVariant(BaseModel):
    answer: str = Field(min_length=2, max_length=1000)
    style_id: str
    target_score: int = Field(ge=0, le=3)
    expected_evidence: Dict[str, EvidenceStatus]
    generation_note: str

class GeneratedBatch(BaseModel):
    variants: List[GeneratedVariant]

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def append_jsonl(path: Path, rows):
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def existing_parent_ids(path: Path):
    if not path.exists():
        return set()
    done = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                done.add(obj["parent_anchor_id"])
    return done

def make_prompt(anchor, question, competency, styles_for_score):
    banned_phrases = [
        "최종 결정은 제가 하겠습니다",
        "최종적으로 제가 결정하겠습니다",
        "AI는 참고자료로 사용하고",
        "그대로 사용하지 않고 확인하겠습니다",
    ]

    payload = {
        "task": "AI 활용 역량 평가용 synthetic answer augmentation",
        "competency": competency,
        "question": question,
        "gold_anchor": {
            "answer": anchor["answer"],
            "score": anchor["score"],
            "evidence": anchor["evidence"],
        },
        "styles_to_generate": styles_for_score,
        "hard_constraints": [
            "각 variant는 gold_anchor와 동일한 target_score를 유지해야 한다.",
            "각 variant는 gold_anchor와 동일한 evidence 수준을 의미상 유지해야 한다.",
            "anchor를 문장 단위로 복사하거나 단순 동의어 치환하지 않는다.",
            "각 variant는 서로 다른 사람이 쓴 것처럼 문장 길이, 어휘, 말투, 문장 구조를 충분히 다르게 만든다.",
            "일부 variant는 짧거나 불완전한 문장, 구어체, 오탈자, 장황한 표현을 자연스럽게 포함할 수 있다.",
            "사용자가 실제로 말하지 않은 evidence를 새로 추가하지 않는다.",
            "키워드가 아니라 행동과 판단의 의미를 보존한다.",
            "아래 고빈도 표현은 가능하면 피한다: " + " / ".join(banned_phrases),
        ],
        "output_rule": "styles_to_generate의 각 style_id마다 정확히 1개 variant를 생성한다."
    }

    return """너는 교육평가 데이터셋의 문장 다양화 전문가다.

목표는 같은 역량 수준을 여러 사람이 서로 다른 방식으로 표현하는 데이터를 만드는 것이다.
이 작업은 정답문장 패턴을 외우게 하기 위한 것이 아니라 의미 일반화를 돕기 위한 데이터 증강이다.

특히:
- score와 evidence를 반드시 유지한다.
- 문장 구조와 어휘만 바꾸는 단순 paraphrase는 금지한다.
- '최종 결정은 내가', '공식 자료 확인' 같은 전형적 문구를 기계적으로 반복하지 않는다.
- 간접 표현, 축약, 구어체, 오탈자, 장황함, 모순형 함정 등 style 조건을 실제로 반영한다.
- 함정형 답변은 겉으로 올바른 단어를 써도 실제 행동은 target_score 수준에 머물러야 한다.

아래 JSON을 바탕으로 variant를 생성하라.

""" + json.dumps(payload, ensure_ascii=False, indent=2)

class GeminiAugmenter:
    def __init__(self, api_key=None, model=None):
        from google import genai
        self.types = __import__("google.genai.types", fromlist=["GenerateContentConfig"])

        api_key = api_key or os.getenv("GEMINI_API_KEY")
        model = model or os.getenv("GEMINI_MODEL")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 필요합니다.")
        if not model:
            raise ValueError("GEMINI_MODEL이 필요합니다.")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt, retries=5):
        last_error = None

        for attempt in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.types.GenerateContentConfig(
                        temperature=0.9,
                        response_mime_type="application/json",
                        response_schema=GeneratedBatch,
                    ),
                )

                parsed = getattr(response, "parsed", None)
                if isinstance(parsed, GeneratedBatch):
                    return parsed
                if parsed is not None:
                    return GeneratedBatch.model_validate(parsed)
                return GeneratedBatch.model_validate_json(response.text)

            except Exception as e:
                last_error = e
                if attempt == retries - 1:
                    break
                wait = min(60, 2 ** attempt + random.random())
                print(f"[retry {attempt+1}/{retries}] {type(e).__name__} -> {wait:.1f}s")
                time.sleep(wait)

        raise RuntimeError(f"generation failed: {type(last_error).__name__}: {last_error}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/expanded_candidates.jsonl")
    parser.add_argument("--limit", type=int, default=None,
                        help="테스트용: 처리할 gold anchor 개수 제한")
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    framework = load_json(DATA_DIR / "competency_framework.json")
    questions = load_json(DATA_DIR / "questions.json")
    styles = load_json(DATA_DIR / "augmentation_styles.json")
    anchors = load_jsonl(DATA_DIR / "gold_anchors.jsonl")

    qidx = {q["question_id"]: q for q in questions}
    cidx = {c["id"]: c for c in framework["competencies"]}

    out_path = BASE_DIR / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = existing_parent_ids(out_path)

    augmenter = GeminiAugmenter()

    pending = [a for a in anchors if a["example_id"] not in done]
    if args.limit is not None:
        pending = pending[:args.limit]

    print(f"pending anchors: {len(pending)}")

    for i, anchor in enumerate(pending, 1):
        q = qidx[anchor["question_id"]]
        comp = cidx[anchor["competency_id"]]
        style_list = styles["styles_by_score"][str(anchor["score"])]

        prompt = make_prompt(anchor, q, comp, style_list)
        batch = augmenter.generate(prompt)

        expected_style_ids = {s["id"] for s in style_list}
        got_style_ids = {v.style_id for v in batch.variants}

        if expected_style_ids != got_style_ids:
            missing = expected_style_ids - got_style_ids
            extra = got_style_ids - expected_style_ids
            raise ValueError(
                f"{anchor['example_id']} style mismatch. missing={missing}, extra={extra}"
            )

        output_rows = []
        for n, variant in enumerate(batch.variants, 1):
            # 모델이 metadata를 임의로 바꾸지 못하게 target은 anchor 기준으로 고정 저장
            output_rows.append({
                "candidate_id": f"{anchor['example_id']}-AUG-{n:02d}",
                "parent_anchor_id": anchor["example_id"],
                "question_id": anchor["question_id"],
                "competency_id": anchor["competency_id"],
                "domain": anchor["domain"],
                "target_score": anchor["score"],
                "target_evidence": anchor["evidence"],
                "answer": variant.answer.strip(),
                "style_id": variant.style_id,
                "generation_note": variant.generation_note,
                "source": "synthetic_llm",
                "human_validated": False,
                "reviewed_score": None,
                "reviewed_evidence": None,
                "reviewer_notes": ""
            })

        append_jsonl(out_path, output_rows)
        print(f"[{i}/{len(pending)}] {anchor['example_id']} -> {len(output_rows)} variants")
        time.sleep(args.sleep)

    print(f"saved: {out_path}")

if __name__ == "__main__":
    main()
