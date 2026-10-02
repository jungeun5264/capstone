# Expanded Dataset v2

이 버전은 72개 기준답안을 그대로 학습 데이터로 사용하는 구조가 아닙니다.

## 핵심 개념

### 1. Gold Anchors
`data/gold_anchors.jsonl`

현재 18문항 × 4점수 = 72개의 기준답안입니다.
이 데이터는 점수 수준을 설명하는 anchor로 사용합니다.

### 2. Synthetic Augmentation
`augment_dataset.py`

각 anchor마다 8가지 서로 다른 언어 스타일의 답변을 생성합니다.

72 anchors × 8 variants = 최대 576 synthetic candidates

Gold 72개까지 합치면 총 648개 규모의 초기 후보 corpus가 됩니다.

중요:
576개는 생성 즉시 정답 데이터가 아닙니다.
반드시 사람이 score와 evidence를 검토해야 합니다.

## 다양성 설계

점수 수준에 따라 style을 다르게 구성했습니다.

예:
- 짧은 구어체
- 간접 표현
- 오탈자/축약이 있는 표현
- 장황한 표현
- 관련 없는 정보가 섞인 표현
- 일부만 맞는 답변
- self-contradictory 답변
- keyword trap
- 정답 문구를 쓰지 않지만 의미상 완전한 답변

목적은 모델이
"최종 결정은 제가 하겠습니다"
같은 표면적 문구를 외우는 것을 방지하는 것입니다.

## 사용 순서

### A. Gemini 준비 전
지금 할 수 있는 것:
- `gold_anchors.jsonl` 검토
- `augmentation_styles.json` 검토
- 문항/rubric 수정
- API/UI 개발

### B. Gemini 인증 후 1개 anchor로 테스트

```bash
python augment_dataset.py --limit 1
```

정상 작동하면 전체 실행:

```bash
python augment_dataset.py
```

`data/expanded_candidates.jsonl` 생성.

기본적으로 이미 생성된 parent anchor는 다시 호출하지 않으므로
503 등으로 중간에 멈춰도 재실행해서 이어갈 수 있습니다.

### C. 다양성/중복 검사

```bash
python quality_control.py
```

생성:
`data/diversity_report.json`

다음 항목을 자동 점검합니다.
- anchor와 지나치게 유사한 답변
- 같은 anchor에서 생성된 near-duplicate
- 반복되는 전형적 문구
- score/style 분포

### D. 사람 검토표 만들기

```bash
python make_review_csv.py
```

생성:
`data/expanded_review.csv`

검토자는 다음을 채웁니다.
- keep
- corrected_score
- corrected_evidence_json
- human_validated
- reviewer_notes

AI가 붙인 target score를 그대로 승인하지 말고
rubric을 보고 직접 판단하는 것을 권장합니다.

### E. 검토 완료 데이터 반영

```bash
python apply_review.py
```

생성:
`data/validated_examples.jsonl`

`keep=TRUE` 이고 `human_validated=TRUE` 인 데이터만 들어갑니다.

### F. Train / Validation / Test 분리

```bash
python split_dataset.py
```

생성:
- `data/train.jsonl`
- `data/validation.jsonl`
- `data/test_unseen_scenarios.jsonl`

Test에는 각 역량의 3번째 문항을 통째로 hold-out 합니다.

- H1-03
- H2-03
- E1-03
- E2-03
- T1-03
- T2-03

따라서 같은 문장의 paraphrase가 train과 test에 동시에 들어가는
데이터 누수 문제를 줄이고, 처음 보는 상황에서도 역량을 평가하는지 볼 수 있습니다.

## 왜 generator의 score를 바로 쓰지 않나?

생성 AI가 target_score를 알고 답변을 만듭니다.
하지만 생성된 문장이 실제로 그 점수 수준에 머무는지는 별개입니다.

예:
1점 답변을 만들라고 했는데 너무 잘 써서 2점이 될 수 있음.

따라서:
generator target -> human review -> corrected label

순서가 필요합니다.

## Fine-tuning 전에 권장

- 두 명 이상의 사람이 일부 데이터를 독립 채점
- 사람 간 점수 일치도 확인
- 실제 사용자 응답 추가
- synthetic 데이터와 실제 응답을 구분
- unseen-scenario test 유지

현재 단계의 목표는 fine-tuning 자체보다
"신뢰 가능한 AI 활용역량 평가 데이터셋"을 만드는 것입니다.
