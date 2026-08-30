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
from AI.predictive import predict_hiring_outcome

logger = logging.getLogger(__name__)

def generate_candidate_explainability(
    candidate: Any,
    job: Any,
    ats_score: Optional[float] = None,
    match_score: Optional[float] = None,
    screening_score: Optional[float] = None,
    ats_details: Optional[Dict[str, Any]] = None,
    score_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates a full 13-point AI Explainability bundle for a candidate:
    - ATS Score
    - Match Score
    - Screening Score
    - Skill Coverage (%)
    - Experience Fit (%)
    - Final Score
    - Hiring Probability
    - Risk Level
    - Strengths
    - Weaknesses
    - Missing Skills
    - Recommendation
    - Explanation
    """
    cand_dict = _normalize_candidate(candidate)
    job_dict = _normalize_job(job)

    # 1. Base Score Resolution
    if score_details is None:
        score_details = calculate_enhanced_score(cand_dict, job_dict)

    if match_score is None:
        match_score = float(score_details.get("match_percentage", 65.0))
    if ats_score is None:
        ats_score = float(cand_dict.get("ats_score") or (ats_details.get("ats_score") if ats_details else match_score))
    if screening_score is None:
        screening_score = float(cand_dict.get("screening_score") or 75.0)

    # Calculate Composite Final Score (30% ATS + 50% Match + 20% Screening)
    final_score = calculate_final_score(
        screening_score=screening_score,
        ats_score=ats_score,
        match_score=match_score
    )

    # 2. Skill Coverage Calculation
    cand_skills = {s.lower() for s in cand_dict.get("skills", []) if isinstance(s, str)}
    job_skills = {s.lower() for s in job_dict.get("required_skills", []) if isinstance(s, str)}
    
    if job_skills:
        matched_count = len(cand_skills & job_skills)
        skill_coverage_pct = round((matched_count / len(job_skills)) * 100.0, 1)
    else:
        skill_coverage_pct = 100.0

    # 3. Experience Fit Calculation
    cand_exp = extract_years(cand_dict.get("experience", 0))
    job_exp = extract_years(job_dict.get("experience", 0))
    if job_exp > 0:
        exp_fit_pct = round(min(120.0, (cand_exp / job_exp) * 100.0), 1)
    else:
        exp_fit_pct = 100.0

    # 4. Predictive Analytics
    pred_res = predict_hiring_outcome(
        candidate=cand_dict,
        job=job_dict,
        final_score=final_score,
        ats_score=ats_score,
        match_score=match_score,
        screening_score=screening_score
    )

    # 5. Extract Strengths, Weaknesses, Missing Skills
    matched_skills = pred_res.get("matched_skills", [])
    missing_skills = pred_res.get("missing_skills", [])
    strengths = pred_res.get("strengths", [])
    weaknesses = pred_res.get("risks", [])

    # 6. Recommendation & Explanation
    hiring_prob = pred_res.get("hiring_probability", 0.7)
    risk_lvl = pred_res.get("risk_level", "Medium")
    rec = pred_res.get("recommendation", "Consider")

    explanation_parts = [
        f"Candidate '{cand_dict.get('name')}' attained an overall composite final score of {final_score}%, comprising a {ats_score}% ATS score, {match_score}% semantic match score, and {screening_score}% initial screening score.",
        f"Skill coverage stands at {skill_coverage_pct}% with {len(matched_skills)} verified core skills ({', '.join(matched_skills[:3]) if matched_skills else 'None'}).",
        f"Experience fit is rated at {exp_fit_pct}% ({cand_exp} actual years vs {job_exp} required years).",
        f"Predictive hiring model forecasts a {pred_res.get('hiring_probability_percentage')} probability of successful hiring outcome with '{risk_lvl}' risk."
    ]
    if missing_skills:
        explanation_parts.append(f"Recommended upskilling focus: {', '.join(missing_skills[:3])}.")

    full_explanation = " ".join(explanation_parts)

    return {
        "candidate_name": cand_dict.get("name", "Candidate"),
        "candidate_email": cand_dict.get("email", "candidate@example.com"),
        "ats_score": round(ats_score, 2),
        "match_score": round(match_score, 2),
        "screening_score": round(screening_score, 2),
        "skill_coverage": skill_coverage_pct,
        "skill_coverage_percentage": f"{skill_coverage_pct}%",
        "experience_fit": exp_fit_pct,
        "experience_fit_percentage": f"{exp_fit_pct}%",
        "final_score": final_score,
        "hiring_probability": hiring_prob,
        "hiring_probability_percentage": pred_res.get("hiring_probability_percentage"),
        "risk_level": risk_lvl,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "recommendation": rec,
        "explanation": full_explanation
    }
