import pytest
from AI.screening import (
    generate_questions,
    evaluate_answer,
    evaluate_answers,
    calculate_final_score
)

def test_generate_questions_with_dict():
    cand = {
        "name": "Jane Doe",
        "skills": ["Python", "FastAPI"],
        "experience": 4
    }
    job = {
        "job_title": "Backend Engineer",
        "required_skills": ["Python", "FastAPI", "Docker", "AWS"],
        "location": "Pune"
    }
    qs = generate_questions(cand, job)
    assert isinstance(qs, dict)
    assert len(qs.get("technical_questions", [])) > 0
    assert len(qs.get("experience_questions", [])) > 0
    assert len(qs.get("availability_questions", [])) > 0
    assert len(qs.get("salary_questions", [])) > 0
    assert len(qs.get("location_questions", [])) > 0
    assert len(qs.get("all_questions", [])) >= 5


def test_generate_questions_with_string_inputs():
    cand_str = "Alice Smith, 5 years Python and PostgreSQL experience"
    job_str = "Senior Backend Developer in Pune, requiring Python, AWS, Docker"
    qs = generate_questions(cand_str, job_str)
    assert isinstance(qs, dict)
    assert len(qs.get("all_questions", [])) >= 3


def test_evaluate_strong_answer():
    cand = {"name": "Bob", "skills": ["Python", "FastAPI"]}
    q = "Can you explain your experience working with FastAPI?"
    a = "I have 4 years of hands-on experience building asynchronous microservices with FastAPI, PostgreSQL, and Docker."
    res = evaluate_answer(cand, q, a)
    assert res["score"] >= 7
    assert res["relevance"] in ["High", "Medium"]
    assert "FastAPI" in a


def test_evaluate_weak_answer():
    cand = {"name": "Bob", "skills": ["Python"]}
    q = "How do you manage database connections in high-load async Python services?"
    a = "I don't know. No experience with that."
    res = evaluate_answer(cand, q, a)
    assert res["score"] <= 3
    assert res["relevance"] == "Low"
    assert len(res["concerns"]) > 0


def test_evaluate_empty_and_whitespace_answer():
    cand = {"name": "Bob"}
    q = "What is your expected CTC?"
    for empty_a in ["", "   ", None, "\n\t"]:
        res = evaluate_answer(cand, q, empty_a)
        assert res["score"] == 0
        assert res["relevance"] == "Low"
        assert len(res["concerns"]) > 0


def test_evaluate_malformed_answer():
    cand = {"name": "Bob"}
    q = "What is your notice period?"
    # Numbers, lists, dicts passed as answer should not throw exceptions
    res1 = evaluate_answer(cand, q, 30)
    assert isinstance(res1, dict)
    assert "score" in res1

    res2 = evaluate_answer(cand, q, ["Immediate", "joiner"])
    assert isinstance(res2, dict)
    assert res2["score"] > 0

    res3 = evaluate_answer(cand, q, {"notice": "15 days"})
    assert isinstance(res3, dict)
    assert res3["score"] > 0


def test_evaluate_answers_batch_list():
    cand = {"name": "Charlie", "skills": ["Python", "Docker"]}
    questions = [
        "Explain your Python background.",
        "What is your notice period?",
        "What is your expected salary?"
    ]
    answers = [
        "I have 5 years building scalable APIs in Python and Django.",
        "30 days notice period.",
        "15 LPA negotiable."
    ]
    res = evaluate_answers(cand, questions, answers)
    assert isinstance(res, dict)
    assert res["screening_score"] >= 60.0
    assert len(res["evaluations"]) == 3
    assert "summary" in res


def test_evaluate_answers_batch_dict():
    cand = {"name": "Charlie"}
    questions = [
        "Explain your Python background.",
        "What is your notice period?"
    ]
    answers = {
        "Explain your Python background.": "5 years of Python development.",
        "What is your notice period?": "Immediate"
    }
    res = evaluate_answers(cand, questions, answers)
    assert res["screening_score"] >= 60.0
    assert len(res["evaluations"]) == 2


def test_calculate_final_score_formula():
    # 30% ATS + 50% Match + 20% Screening
    # Test 1: ATS=80, Match=90, Screening=70
    # Final = (0.30 * 80) + (0.50 * 90) + (0.20 * 70) = 24 + 45 + 14 = 83.0
    score1 = calculate_final_score(ats_score=80.0, match_score=90.0, screening_score=70.0)
    assert score1 == 83.0

    # Test 2: ATS=100, Match=100, Screening=100 -> 100.0
    score2 = calculate_final_score(ats_score=100.0, match_score=100.0, screening_score=100.0)
    assert score2 == 100.0

    # Test 3: ATS=0, Match=0, Screening=0 -> 0.0
    score3 = calculate_final_score(ats_score=0.0, match_score=0.0, screening_score=0.0)
    assert score3 == 0.0

    # Test 4: 0-10 scale auto-conversion
    score4 = calculate_final_score(ats_score=8.0, match_score=9.0, screening_score=7.0)
    assert score4 == 83.0
