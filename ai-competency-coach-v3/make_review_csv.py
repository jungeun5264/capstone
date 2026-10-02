import argparse
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_jsonl(path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/expanded_candidates.jsonl")
    parser.add_argument("--output", default="data/expanded_review.csv")
    args = parser.parse_args()

    rows = load_jsonl(BASE_DIR / args.input)
    out = BASE_DIR / args.output

    fields = [
        "candidate_id", "parent_anchor_id", "question_id", "competency_id", "domain",
        "style_id", "target_score", "answer", "target_evidence_json",
        "keep", "corrected_score", "corrected_evidence_json",
        "human_validated", "reviewer_notes"
    ]

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()

        for r in rows:
            w.writerow({
                "candidate_id": r["candidate_id"],
                "parent_anchor_id": r["parent_anchor_id"],
                "question_id": r["question_id"],
                "competency_id": r["competency_id"],
                "domain": r["domain"],
                "style_id": r["style_id"],
                "target_score": r["target_score"],
                "answer": r["answer"],
                "target_evidence_json": json.dumps(r["target_evidence"], ensure_ascii=False),
                "keep": "",
                "corrected_score": "",
                "corrected_evidence_json": "",
                "human_validated": "",
                "reviewer_notes": ""
            })

    print(out)

if __name__ == "__main__":
    main()
