import argparse
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

COMMON_PHRASES = [
    "최종 결정은 제가",
    "최종적으로 제가 결정",
    "AI는 참고자료",
    "그대로 사용하지 않고",
    "공식 자료에서 확인",
]

def load_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def normalize(text):
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text

def sim(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/expanded_candidates.jsonl")
    parser.add_argument("--gold", default="data/gold_anchors.jsonl")
    parser.add_argument("--report", default="data/diversity_report.json")
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.86)
    args = parser.parse_args()

    candidates = load_jsonl(BASE_DIR / args.input)
    gold = load_jsonl(BASE_DIR / args.gold)
    gold_map = {x["example_id"]: x for x in gold}

    issues = []
    style_counts = Counter()
    score_counts = Counter()
    phrase_counts = Counter()

    by_parent = defaultdict(list)
    for row in candidates:
        by_parent[row["parent_anchor_id"]].append(row)

    for row in candidates:
        style_counts[row["style_id"]] += 1
        score_counts[str(row["target_score"])] += 1

        ans = row["answer"]
        for phrase in COMMON_PHRASES:
            if phrase in ans:
                phrase_counts[phrase] += 1
                issues.append({
                    "candidate_id": row["candidate_id"],
                    "type": "repeated_formula_phrase",
                    "detail": phrase
                })

        anchor = gold_map.get(row["parent_anchor_id"])
        if anchor:
            s = sim(ans, anchor["answer"])
            if s >= args.near_duplicate_threshold:
                issues.append({
                    "candidate_id": row["candidate_id"],
                    "type": "too_similar_to_anchor",
                    "detail": round(s, 3)
                })

    # Same-parent near duplicates
    for parent_id, rows in by_parent.items():
        for i in range(len(rows)):
            for j in range(i+1, len(rows)):
                s = sim(rows[i]["answer"], rows[j]["answer"])
                if s >= args.near_duplicate_threshold:
                    issues.append({
                        "candidate_id": rows[j]["candidate_id"],
                        "type": "near_duplicate_sibling",
                        "detail": {
                            "other": rows[i]["candidate_id"],
                            "similarity": round(s, 3)
                        }
                    })

    report = {
        "n_candidates": len(candidates),
        "n_parents": len(by_parent),
        "style_counts": dict(style_counts),
        "score_counts": dict(score_counts),
        "common_phrase_counts": dict(phrase_counts),
        "n_issues": len(issues),
        "issues": issues
    }

    out = BASE_DIR / args.report
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"candidates: {len(candidates)}")
    print(f"issues: {len(issues)}")
    print(f"report: {out}")

if __name__ == "__main__":
    main()
