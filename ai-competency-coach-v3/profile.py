from collections import defaultdict
from dataset import competency_index

def build_profile(evaluations: list[dict]) -> dict:
    grouped = defaultdict(list)

    for row in evaluations:
        grouped[row["competency_id"]].append(row["score"])

    cidx = competency_index()
    result = {}

    for cid, scores in grouped.items():
        mean = sum(scores) / len(scores)
        result[cid] = {
            "name": cidx[cid]["name"],
            "domain": cidx[cid]["domain"],
            "n_questions": len(scores),
            "mean_0_to_3": round(mean, 3),
            "percent": round(mean / 3 * 100, 1),
        }

    overall = (
        sum(x["score"] for x in evaluations) / len(evaluations)
        if evaluations else 0
    )

    return {
        "overall_mean_0_to_3": round(overall, 3),
        "overall_percent": round(overall / 3 * 100, 1),
        "competencies": result
    }
