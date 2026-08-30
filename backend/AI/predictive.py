import os
import sys
import logging
from typing import Dict, Any, List, Optional, Union

# Add paths
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ai_dir = os.path.abspath(os.path.dirname(__file__))
for p in [backend_dir, ai_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from AI.screening import _normalize_candidate, _normalize_job, calculate_final_score
from AI.scorer import calculate_enhanced_score, extract_years

logger = logging.getLogger(__name__)

def predict_hiring_outcome(
    candidate: Any,
    job: Any,
    final_score: Optional[float] = None,
    ats_score: Optional[float] = None,
    match_score: Optional[float] = None,
    screening_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Predicts candidate hiring probability, risk level, strengths, and risks based on:
    Final Score = 30% ATS + 50% Match + 20% Screening.
    Returns structured predictive analytics.
    """
    cand_dict = _normalize_candidate(candidate)
    job_dict = _normalize_job(job)

    # 1. Compute scores if not directly provided
    if final_score is None:
        if ats_score is None or match_score is None or screening_score is None:
            scorer_res = calculate_enhanced_score(cand_dict, job_dict)
            calc_match = float(scorer_res.get("match_percentage", 65.0))
            calc_ats = float(cand_dict.get("ats_score") or calc_match)
            calc_scr = float(cand_dict.get("screening_score") or 75.0)
            
            ats_score = ats_score or calc_ats
            match_score = match_score or calc_match
            screening_score = screening_score or calc_scr
            
        final_score = calculate_final_score(
            screening_score=screening_score,
            ats_score=ats_score,
            match_score=match_score
        )

    # 2. Probability and Risk Calculation
    # Scale: Final Score -> Predictive Probability & Risk Categorization
    if final_score >= 80.0:
        # High success probability (80% - 98%)
        probability = round(min(0.98, 0.80 + (final_score - 80.0) * 0.009), 2)
        hiring_probability_category = "High"
        risk_level = "Low"
        recommendation = "Strong Hire"
        base_explanation = f"Candidate shows exceptional overall alignment with a final composite score of {final_score}%."
    elif final_score >= 60.0:
        # Medium success probability (60% - 79%)
        probability = round(0.60 + (final_score - 60.0) * 0.0095, 2)
        hiring_probability_category = "Medium"
        risk_level = "Medium"
        recommendation = "Consider / Advance to Interview"
        base_explanation = f"Candidate demonstrates solid fundamental skills ({final_score}% composite score) with manageable skill or experience gaps."
    else:
        # Low success probability (10% - 59%)
        probability = round(max(0.10, 0.20 + (final_score / 60.0) * 0.35), 2)
        hiring_probability_category = "Low"
        risk_level = "High"
        recommendation = "Do Not Advance / Reject"
        base_explanation = f"Candidate scores below required operational benchmark with a {final_score}% final score."

    # 3. Analyze Strengths and Risks
    cand_skills = {s.lower() for s in cand_dict.get("skills", []) if isinstance(s, str)}
    job_skills = {s.lower() for s in job_dict.get("required_skills", []) if isinstance(s, str)}
    
    matched_skills = [s for s in job_dict.get("required_skills", []) if isinstance(s, str) and s.lower() in cand_skills]
    missing_skills = [s for s in job_dict.get("required_skills", []) if isinstance(s, str) and s.lower() not in cand_skills]

    cand_exp = extract_years(cand_dict.get("experience", 0))
    job_exp = extract_years(job_dict.get("experience", 0))

    strengths = []
    risks = []

    # Skill insights
    if matched_skills:
        strengths.append(f"Strong match in core skills: {', '.join(matched_skills[:4])}")
    if len(matched_skills) >= max(1, int(len(job_skills) * 0.75)):
        strengths.append("High overall skill coverage (>75% required tech stack).")

    if missing_skills:
        risks.append(f"Missing critical required skills: {', '.join(missing_skills[:3])}")

    # Experience insights
    if cand_exp >= job_exp:
        strengths.append(f"Exceeds minimum experience requirement ({cand_exp} yrs vs {job_exp} yrs required).")
    elif cand_exp < job_exp:
        risks.append(f"Experience deficit ({cand_exp} yrs actual vs {job_exp} yrs target).")

    # Education insights
    edu = str(cand_dict.get("education", "")).lower()
    if any(deg in edu for deg in ["master", "m.tech", "ph.d", "b.tech", "b.e"]):
        strengths.append("Strong academic qualification in computer science / engineering.")

    # Project insights
    projects = cand_dict.get("projects", [])
    if isinstance(projects, list) and len(projects) >= 2:
        strengths.append(f"Demonstrated practical track record with {len(projects)} listed projects.")

    # Employment gap
    if cand_dict.get("employment_gap"):
        risks.append("Identified career / employment gap requiring interview clarification.")

    if not strengths:
        strengths.append("Basic candidate profile provided.")
    if not risks:
        risks.append("No significant hiring risks detected.")

    explanation = f"{base_explanation} Key drivers: {len(strengths)} positive indicators, {len(risks)} identified risks."

    return {
        "candidate": cand_dict.get("name", "Candidate"),
        "final_score": final_score,
        "hiring_probability": probability,
        "hiring_probability_percentage": f"{int(probability * 100)}%",
        "hiring_probability_category": hiring_probability_category,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "strengths": strengths,
        "risks": risks,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "explanation": explanation,
        "model_version": "RecruiterAI-Predictive-v2.0"
    }


def get_sample_frontend_output() -> List[Dict[str, Any]]:
    """
    Returns sample candidate evaluation outputs across High, Medium, and Low tiers
    ready for frontend rendering and technical presentations.
    """
    sample_candidates = [
        {
            "name": "Sarah Jenkins",
            "email": "sarah.j@example.com",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"],
            "experience": 6,
            "education": "Master of Science in Computer Science",
            "projects": ["Distributed Task Queue", "Microservice Gateway"],
            "ats_score": 92.0,
            "match_score": 88.0,
            "screening_score": 90.0
        },
        {
            "name": "Alex Rivera",
            "email": "alex.r@example.com",
            "skills": ["Python", "Flask", "SQL"],
            "experience": 3,
            "education": "Bachelor of Technology",
            "projects": ["Web Scraper Dashboard"],
            "ats_score": 68.0,
            "match_score": 64.0,
            "screening_score": 70.0
        },
        {
            "name": "Jordan Smith",
            "email": "jordan.s@example.com",
            "skills": ["HTML", "CSS"],
            "experience": 1,
            "education": "High School Diploma",
            "projects": [],
            "ats_score": 40.0,
            "match_score": 35.0,
            "screening_score": 45.0
        }
    ]

    target_job = {
        "job_title": "Senior Python Backend Engineer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": 4,
        "location": "Pune"
    }

    results = []
    for cand in sample_candidates:
        res = predict_hiring_outcome(
            candidate=cand,
            job=target_job,
            ats_score=cand["ats_score"],
            match_score=cand["match_score"],
            screening_score=cand["screening_score"]
        )
        results.append(res)

    return results
