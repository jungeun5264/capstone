# GitHub에 올릴 때 — 이것만 보면 됨

## 먼저 이해할 것

`v2`, `v3`는 GitHub 기능 이름이 아닙니다.

제가 만든 프로젝트 파일의 버전을 구분하기 위해 붙인 이름일 뿐입니다.

따라서 사용자가 v2를 v3로 "변환"할 필요가 없습니다.

**v3 ZIP을 풀어서 현재 GitHub 프로젝트 파일 대신 넣으면 됩니다.**

## 가장 쉬운 방법

### 1. 현재 GitHub 저장소는 지우지 마세요.
그냥 현재 상태를 그대로 둡니다.

### 2. `ai-competency-coach-v3.zip`을 다운로드하고 압축을 풉니다.

압축을 풀면 `ai-competency-coach-v3` 폴더가 나옵니다.

### 3. 현재 GitHub 저장소를 PC로 내려받습니다.

GitHub 저장소 페이지에서:

`Code` → `Download ZIP`

다운로드한 현재 저장소 ZIP도 압축을 풉니다.

### 4. 현재 저장소 폴더 안의 기존 프로젝트 파일을 v3 파일로 교체합니다.

쉽게 말하면:

현재 GitHub에서 내려받은 프로젝트 폴더 안의
기존 `app.py`, `api.py`, `data/`, `providers/` 등을 지우고

`ai-competency-coach-v3` 안의 파일들을 전부 복사해서 넣습니다.

`.git` 폴더를 직접 만질 필요는 없습니다.

### 5. 다시 GitHub에 업로드

GitHub 저장소 페이지에서:

`Add file` → `Upload files`

v3 파일들을 업로드한 뒤:

Commit message:
`Update AI competency evaluation framework`

`Commit changes`

를 누릅니다.

## 만약 GitHub Desktop을 쓸 수 있다면 더 쉬움

1. GitHub Desktop에서 현재 저장소 Clone
2. 로컬 저장소 폴더 열기
3. 기존 프로젝트 파일을 v3 파일로 교체
4. GitHub Desktop에서 변경 파일 확인
5. Commit
6. Push origin

이 방법이 파일이 많을 때 더 편합니다.

## 이번 v3에서 달라진 핵심

`data/source_framework.json`
- Word 파일에서 정리한 UNESCO + DigComp 기반 6개 기준
- 이 파일이 평가의 최상위 기준

`data/operational_rubric.json`
- 위 6개 기준을 실제 AI가 채점할 수 있게 쪼갠 evidence + 0~3 rubric

`data/gold_anchors.jsonl`
- 점수별 대표 예시
- 평가기준 자체가 아니라 보조 예시

즉:

source_framework
→ operational_rubric
→ gold_anchors
→ expanded examples

순서입니다.

## Gemini 인증 전

아무 설정을 안 하면 기본 `mock` 모드로 동작하도록 되어 있습니다.

따라서 먼저 GitHub/Streamlit에서 구조와 화면을 테스트하고,
Gemini 인증이 끝난 뒤 실제 Judge를 연결하면 됩니다.
