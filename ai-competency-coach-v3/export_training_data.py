import json
from pathlib import Path
from dataset import load_examples, question_index, competency_index
from prompt_builder import JUDGE_SYSTEM_PROMPT

BASE_DIR = Path(__file__).resolve().parent

def export_messages_jsonl(
    output_path: str = "data/training_ready_messages.jsonl",
    validated_only: bool = False
):
    """
    provider-neutral messages JSONL 생성.
    특정 업체 API에 그대로 업로드하는 파일이라는 뜻은 아니다.
    실제 fine-tuning 전에는 human_validated=True 데이터만 쓰는 것을 권장한다.
    """
    qidx = question_index()
    cidx = competency_index()
    examples = load_examples()

    if validated_only:
        examples = [x for x in examples if x.get("human_validated") is True]

    out = BASE_DIR / output_path

    with out.open("w", encoding="utf-8") as f:
        for ex in examples:
            q = qidx[ex["question_id"]]
            comp = cidx[ex["competency_id"]]

            user_payload = {
                "competency": comp,
                "scenario": q["scenario"],
                "question": q["question"],
                "answer": ex["answer"]
            }

            assistant_payload = {
                "question_id": ex["question_id"],
                "competency_id": ex["competency_id"],
                "score": ex["score"],
                "evidence": ex["evidence"]
            }

            row = {
                "messages": [
                    {"role":"system","content":JUDGE_SYSTEM_PROMPT},
                    {"role":"user","content":json.dumps(user_payload,ensure_ascii=False)},
                    {"role":"assistant","content":json.dumps(assistant_payload,ensure_ascii=False)}
                ]
            }

            f.write(json.dumps(row,ensure_ascii=False) + "\n")

    return str(out)

if __name__ == "__main__":
    print(export_messages_jsonl())
