from collections import Counter, defaultdict
from dataset import load_framework, load_questions, load_examples

fw = load_framework()
questions = load_questions()
examples = load_examples()

assert len(fw["competencies"]) == 6
assert len(questions) == 18
assert len(examples) == 72

per_q = Counter(x["question_id"] for x in examples)
for q in questions:
    assert per_q[q["question_id"]] == 4

for q in questions:
    scores = sorted(
        x["score"] for x in examples
        if x["question_id"] == q["question_id"]
    )
    assert scores == [0,1,2,3]

per_comp = defaultdict(list)
for q in questions:
    per_comp[q["competency_id"]].append(q["question_id"])
assert all(len(v) == 3 for v in per_comp.values())

print("Dataset validation OK")
print("6 competencies / 18 questions / 72 labeled examples")
