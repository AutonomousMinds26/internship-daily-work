import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def calculate_adverse_impact_ratio(
    total_protected: int,
    selected_protected: int,
    total_majority: int,
    selected_majority: int
) -> Dict[str, Any]:
    """
    Calculates the 4/5ths (80%) Adverse Impact Ratio according to standard EEOC and algorithmic fairness guidelines.
    Adverse impact is detected if the selection rate for a protected group is less than 80% (0.80) of the majority group.
    """
    if total_protected == 0 or total_majority == 0:
        return {
            "adverse_impact_ratio": 1.0,
            "has_adverse_impact": False,
            "status": "Insufficient Data",
            "protected_selection_rate": 0.0,
            "majority_selection_rate": 0.0,
            "disparity_ratio": 1.0
        }

    protected_rate = selected_protected / total_protected
    majority_rate = selected_majority / total_majority

    if majority_rate == 0:
        ratio = 1.0
    else:
        ratio = protected_rate / majority_rate

    has_adverse_impact = ratio < 0.80

    return {
        "adverse_impact_ratio": round(ratio, 3),
        "disparity_ratio": round(ratio, 3),
        "has_adverse_impact": has_adverse_impact,
        "protected_selection_rate": round(protected_rate * 100, 2),
        "majority_selection_rate": round(majority_rate * 100, 2),
        "status": "Adverse Impact Detected (< 80%)" if has_adverse_impact else "Compliant (>= 80%)"
    }


def analyze_diversity_pipeline(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes an entire candidate pool for diversity distribution and fairness metrics.
    """
    total = len(candidates)
    if total == 0:
        return {
            "total_candidates": 0,
            "gender_distribution": {},
            "ethnicity_distribution": {},
            "four_fifths_compliance": True,
            "fairness_alert": None
        }

    gender_counts = {}
    gender_selected = {}
    ethnicity_counts = {}
    ethnicity_selected = {}

    for c in candidates:
        g = c.get("gender") or "Not Specified"
        e = c.get("ethnicity") or "Not Specified"
        status = c.get("status", "Applied")
        is_selected = status in ["Selected", "Hired", "Offer", "Offered", "Interview"]

        gender_counts[g] = gender_counts.get(g, 0) + 1
        if is_selected:
            gender_selected[g] = gender_selected.get(g, 0) + 1

        ethnicity_counts[e] = ethnicity_counts.get(e, 0) + 1
        if is_selected:
            ethnicity_selected[e] = ethnicity_selected.get(e, 0) + 1

    # 4/5ths check between Female (protected) and Male (majority) if available
    female_total = gender_counts.get("Female", 0)
    female_sel = gender_selected.get("Female", 0)
    male_total = gender_counts.get("Male", 0)
    male_sel = gender_selected.get("Male", 0)

    ai_metrics = calculate_adverse_impact_ratio(
        total_protected=female_total,
        selected_protected=female_sel,
        total_majority=male_total,
        selected_majority=male_sel
    )

    fairness_alert = None
    if ai_metrics["has_adverse_impact"] and (female_total > 5 and male_total > 5):
        fairness_alert = (
            f"Adverse Impact Warning: Female candidate selection rate ({ai_metrics['protected_selection_rate']}%) "
            f"is below 80% of Male candidate selection rate ({ai_metrics['majority_selection_rate']}%). "
            f"Ratio: {ai_metrics['adverse_impact_ratio']}."
        )

    return {
        "total_candidates": total,
        "gender_distribution": {k: {"count": v, "selected": gender_selected.get(k, 0)} for k, v in gender_counts.items()},
        "ethnicity_distribution": {k: {"count": v, "selected": ethnicity_selected.get(k, 0)} for k, v in ethnicity_counts.items()},
        "adverse_impact_analysis": ai_metrics,
        "four_fifths_compliance": not ai_metrics["has_adverse_impact"],
        "fairness_alert": fairness_alert
    }
