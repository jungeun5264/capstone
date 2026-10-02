import argparse
import json
from collections import Counter, defaultdict
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
    parser.add_argument("--input", default="data/validated_examples.jsonl")
    args = parser.parse_args()

    path = BASE_DIR / args.input
    rows = load_jsonl(path)

    print("N =", len(rows))
    print("scores =", Counter(r["score"] for r in rows))
    print("competencies =", Counter(r["competency_id"] for r in rows))
    print("styles =", Counter(r.get("style_id", "unknown") for r in rows))

    by_q = defaultdict(list)
    for r in rows:
        by_q[r["question_id"]].append(r)

    print("\nper question")
    for qid in sorted(by_q):
        print(qid, len(by_q[qid]), Counter(r["score"] for r in by_q[qid]))

if __name__ == "__main__":
    main()
