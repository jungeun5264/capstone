import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def load_source_framework():
    return json.loads((DATA_DIR / "source_framework.json").read_text(encoding="utf-8"))

def load_operational_rubric():
    return json.loads((DATA_DIR / "operational_rubric.json").read_text(encoding="utf-8"))

# Backward compatibility: 기존 코드에서 load_framework()를 호출해도 작동
def load_framework():
    return load_operational_rubric()

def load_questions():
    return json.loads((DATA_DIR / "questions.json").read_text(encoding="utf-8"))

def load_examples():
    rows = []
    with (DATA_DIR / "gold_anchors.jsonl").open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def question_index():
    return {q["question_id"]: q for q in load_questions()}

def source_competency_index():
    return {c["id"]: c for c in load_source_framework()["competencies"]}

def competency_index():
    return {c["id"]: c for c in load_operational_rubric()["competencies"]}

def examples_for_question(question_id: str):
    return [x for x in load_examples() if x["question_id"] == question_id]

def examples_for_competency(competency_id: str):
    return [x for x in load_examples() if x["competency_id"] == competency_id]
