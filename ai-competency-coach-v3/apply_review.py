import argparse
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TRUE_VALUES = {"true", "1", "yes", "y", "keep", "o", "ok"}

def is_true(value):
    return str(value).strip().lower() in TRUE_VALUES

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", default="data/expanded_review.csv")
    parser.add_argument("--output", default="data/validated_examples.jsonl")
    args = parser.parse_args()

    review_path = BASE_DIR / args.review
    out_path = BASE_DIR / args.output

    kept = 0
    with review_path.open(encoding="utf-8-sig") as f, out_path.open("w", encoding="utf-8") as out:
        reader = csv.DictReader(f)

        for row in reader:
            if not is_true(row.get("keep", "")):
                continue
            if not is_true(row.get("human_validated", "")):
                continue

            score = int(row["corrected_score"]) if row["corrected_score"].strip() else int(row["target_score"])
            evidence_text = row["corrected_evidence_json"].strip() or row["target_evidence_json"]
            evidence = json.loads(evidence_text)

            obj = {
                "example_id": row["candidate_id"],
                "parent_anchor_id": row["parent_anchor_id"],
                "question_id": row["question_id"],
                "competency_id": row["competency_id"],
                "domain": row["domain"],
                "answer": row["answer"],
                "score": score,
                "evidence": evidence,
                "style_id": row["style_id"],
                "source": "synthetic_llm_human_validated",
                "human_validated": True,
                "reviewer_notes": row.get("reviewer_notes", "")
            }

            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            kept += 1

    print(f"validated examples: {kept}")
    print(out_path)

if __name__ == "__main__":
    main()
