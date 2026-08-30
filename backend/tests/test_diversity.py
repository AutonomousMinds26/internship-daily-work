import pytest
from AI.diversity import generate_diversity_and_aggregate_insights

def test_diversity_insights_aggregate():
    candidates = [
        {"name": "Cand 1", "final_score": 85.0, "experience": 5, "skills": ["Python", "FastAPI"], "status": "Shortlisted"},
        {"name": "Cand 2", "final_score": 72.0, "experience": 3, "skills": ["Python", "Docker"], "status": "Interview"},
        {"name": "Cand 3", "final_score": 45.0, "experience": 1, "skills": ["HTML"], "status": "Rejected"}
    ]
    insights = generate_diversity_and_aggregate_insights(candidates)
    assert insights["total_candidates"] == 3
    assert insights["average_final_score"] == pytest.approx(67.33, rel=0.1)
    assert insights["score_tiers"]["High (>=80%)"] == 1
    assert insights["score_tiers"]["Medium (60-79%)"] == 1
    assert insights["score_tiers"]["Low (<60%)"] == 1
    assert insights["fairness_audit"]["demographic_neutrality_verified"] is True


def test_diversity_insights_empty():
    insights = generate_diversity_and_aggregate_insights([])
    assert insights["total_candidates"] == 0
    assert insights["fairness_audit"]["demographic_neutrality_verified"] is True
