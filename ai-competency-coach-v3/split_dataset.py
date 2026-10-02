import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Third scenario of every competency is held out as unseen-scenario test.
STRICT_TEST_QUESTIONS = {
    "H1-03", "H2-03", "E1-03", "E2-03", "T1-03", "T2-03"
}

def load_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def dump_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validated", default="data/validated_examples.jsonl")
    parser.add_argument("--gold", default="data/gold_anchors.jsonl")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    gold = load_jsonl(BASE_DIR / args.gold)
    validated = load_jsonl(BASE_DIR / args.validated)

    # gold anchor도 확정 전이라면 별도 human validation을 권장.
    rows = []
    for g in gold:
        r = dict(g)
        r["source"] = r.get("source", "gold_anchor")
        rows.append(r)
    rows.extend(validated)

    test = [r for r in rows if r["question_id"] in STRICT_TEST_QUESTIONS]
    train_pool = [r for r in rows if r["question_id"] not in STRICT_TEST_QUESTIONS]

    # validation은 같은 parent_anchor family가 train/val에 동시에 들어가지 않도록 그룹 단위 분리
    groups = defaultdict(list)
    for r in train_pool:
        group_id = r.get("parent_anchor_id") or r.get("example_id")
        groups[group_id].append(r)

    group_ids = list(groups)
    rng.shuffle(group_ids)

    n_val = max(1, round(len(group_ids) * 0.15))
    val_ids = set(group_ids[:n_val])

    train, val = [], []
    for gid, group_rows in groups.items():
        (val if gid in val_ids else train).extend(group_rows)

    dump_jsonl(DATA_DIR / "train.jsonl", train)
    dump_jsonl(DATA_DIR / "validation.jsonl", val)
    dump_jsonl(DATA_DIR / "test_unseen_scenarios.jsonl", test)

    print("train:", len(train))
    print("validation:", len(val))
    print("test_unseen_scenarios:", len(test))
    print("held-out questions:", sorted(STRICT_TEST_QUESTIONS))

if __name__ == "__main__":
    main()
