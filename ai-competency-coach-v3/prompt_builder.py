import json
from dataset import (
    question_index,
    competency_index,
    source_competency_index,
    examples_for_question,
    examples_for_competency,
)

JUDGE_SYSTEM_PROMPT = """
너는 AI 활용 역량 평가 Judge다.

가장 중요한 원칙:
- 평가의 최상위 기준은 source_framework의 criterion이다.
- operational rubric과 gold anchors는 그 criterion을 실제로 판단하기 위한 보조 수단이다.
- 예시답안의 특정 문구를 외워서 채점하지 않는다.
- 답변의 실제 의미와 행동을 평가한다.

규칙:
1. source criterion을 최우선으로 본다.
2. evidence는 absent / partial / clear 중 하나로 판정한다.
3. score는 evidence 개수의 단순 합이 아니라 rubric 전체 수준을 적용한다.
4. 문장 길이, 말투, 특정 키워드 유무만으로 점수를 주지 않는다.
5. 사용자가 말하지 않은 행동을 가정하지 않는다.
6. feedback에는 잘한 점과 보완점을 모두 포함한다.
7. 한국어로 평가한다.
8. 반드시 JSON만 반환한다. 마크다운 코드블록은 사용하지 않는다.
"""

def build_fewshot_prompt(question_id: str, answer: str) -> str:
    qidx = question_index()
    opidx = competency_index()
    srcidx = source_competency_index()

    if question_id not in qidx:
        raise KeyError(f"Unknown question_id: {question_id}")

    q = qidx[question_id]
    cid = q["competency_id"]
    operational = opidx[cid]
    source = srcidx[cid]

    anchors = sorted(
        examples_for_question(question_id),
        key=lambda x: x["score"]
    )

    others = [
        x for x in examples_for_competency(cid)
        if x["question_id"] != question_id
    ]
    cross = []
    for score in range(4):
        candidates = [x for x in others if x["score"] == score]
        if candidates:
            cross.append(candidates[0])

    payload = {
        "source_framework": source,
        "operational_rubric": operational,
        "question": q,
        "gold_anchors_same_question": [
            {
                "score": x["score"],
                "answer": x["answer"],
                "evidence": x["evidence"]
            }
            for x in anchors
        ],
        "cross_domain_examples_same_competency": [
            {
                "score": x["score"],
                "answer": x["answer"],
                "evidence": x["evidence"]
            }
            for x in cross
        ],
        "new_answer_to_evaluate": answer
    }

    evidence_ids = [x["id"] for x in operational["evidence"]]

    output_format = {
        "question_id": q["question_id"],
        "competency_id": cid,
        "score": "0~3 정수",
        "evidence": {
            evidence_id: "absent | partial | clear"
            for evidence_id in evidence_ids
        },
        "reason": "채점 근거를 한국어로 작성",
        "feedback": "잘한 점과 보완할 점을 한국어로 작성",
        "next_step": "다음 답변에서 바로 적용할 행동 한 가지",
        "confidence": "0.0~1.0 숫자"
    }

    return (
        JUDGE_SYSTEM_PROMPT
        + "\n\n아래 자료에서 source_framework의 criterion을 가장 우선하여 평가하라.\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\n반드시 아래 JSON 구조와 동일한 키로만 반환하라.\n"
        + json.dumps(output_format, ensure_ascii=False, indent=2)
    )
