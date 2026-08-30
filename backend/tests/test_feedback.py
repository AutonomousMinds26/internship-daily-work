import pytest
from AI.feedback_analyzer import analyze_feedback

def test_analyze_positive_feedback():
    feedbacks = [
        {"rating": 5, "comment": "Excellent technical depth in Python and system design. Very strong communication."},
        {"rating": 4, "comment": "Great problem-solving skills during live coding round."}
    ]
    res = analyze_feedback(feedbacks)
    assert res["average_rating"] >= 4.0
    assert len(res["positive_points"]) > 0
    assert "feedback" in res["overall_feedback"].lower() or len(res["overall_feedback"]) > 10


def test_analyze_mixed_feedback():
    feedbacks = [
        {"rating": 4, "comment": "Strong Python fundamentals and clean code style."},
        {"rating": 2, "comment": "Lacks experience with AWS infrastructure and Docker containerization."}
    ]
    res = analyze_feedback(feedbacks)
    assert 2.5 <= res["average_rating"] <= 3.5
    assert len(res["concerns"]) > 0


def test_analyze_empty_feedback():
    res = analyze_feedback([])
    assert res["average_rating"] == 0.0
    assert len(res["concerns"]) > 0
