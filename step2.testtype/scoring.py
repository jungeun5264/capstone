from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Tuple


ABILITY_META = {
    "ai_basic": {
        "label": "AI의 기초 이해",
        "criteria": ["limitations_awareness", "uncertainty_awareness", "appropriate_use"],
    },
    "ai_usage": {
        "label": "AI 활용 능력",
        "criteria": ["goal_definition", "context_constraints", "iterative_refinement"],
    },
    "human_agency": {
        "label": "인간의 주도권",
        "criteria": ["criteria_setting", "critical_selection", "decision_ownership"],
    },
    "human_responsibility": {
        "label": "인간의 책임",
        "criteria": ["verification", "uncertainty_handling", "final_review"],
    },
    "ethical_view": {
        "label": "윤리적 관점",
        "criteria": ["bias_fairness", "stakeholder_impact", "honest_use"],
    },
    "safe_use": {
        "label": "안전하고 책임 있는 사용",
        "criteria": ["privacy", "confidentiality", "risk_management"],
    },
}

ABILITY_ORDER = list(ABILITY_META.keys())


def ability_score(result: Dict[str, Any], key: str) -> int | None:
    block = result.get(key, {})
    if not block.get("evaluated", False):
        return None
    criteria = ABILITY_META[key]["criteria"]
    values = [int(block.get(c, 0)) for c in criteria]
    return round(sum(values) / (len(values) * 4) * 100)


def all_ability_scores(result: Dict[str, Any]) -> Dict[str, int | None]:
    return {key: ability_score(result, key) for key in ABILITY_ORDER}


def overall_score(result: Dict[str, Any]) -> int:
    vals = [v for v in all_ability_scores(result).values() if v is not None]
    return round(sum(vals) / len(vals)) if vals else 0


def update_profile(
    baseline_profile: Dict[str, int],
    result: Dict[str, Any],
) -> Dict[str, int]:
    """For the prototype, assessed abilities display the current mission score.
    Unassessed abilities retain the existing profile score.
    In production, replace this with the project's longitudinal update rule.
    """
    profile = deepcopy(baseline_profile)
    scores = all_ability_scores(result)
    for key, score in scores.items():
        if score is not None:
            profile[key] = score
    return profile


def strongest_assessed(result: Dict[str, Any]) -> Tuple[str, int] | None:
    pairs = [(k, s) for k, s in all_ability_scores(result).items() if s is not None]
    if not pairs:
        return None
    key, score = max(pairs, key=lambda x: x[1])
    return ABILITY_META[key]["label"], score


def weakest_assessed(result: Dict[str, Any]) -> Tuple[str, int] | None:
    pairs = [(k, s) for k, s in all_ability_scores(result).items() if s is not None]
    if not pairs:
        return None
    key, score = min(pairs, key=lambda x: x[1])
    return ABILITY_META[key]["label"], score


def biggest_growth(prev: Dict[str, Any], curr: Dict[str, Any]) -> Tuple[str, int, int, int] | None:
    prev_scores = all_ability_scores(prev)
    curr_scores = all_ability_scores(curr)
    candidates: List[Tuple[str, int, int, int]] = []
    for key in ABILITY_ORDER:
        p = prev_scores[key]
        c = curr_scores[key]
        if p is not None and c is not None:
            candidates.append((key, p, c, c - p))
    if not candidates:
        return None
    key, p, c, delta = max(candidates, key=lambda x: x[3])
    return ABILITY_META[key]["label"], p, c, delta


def evaluated_labels(result: Dict[str, Any]) -> List[str]:
    scores = all_ability_scores(result)
    return [ABILITY_META[k]["label"] for k, v in scores.items() if v is not None]
