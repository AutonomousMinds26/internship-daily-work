from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional, cast
import logging
import uuid

from app.database import get_db
from app.models import Candidate, Job, CandidateScore, Recommendation, Interview, InterviewSlot, CandidateHistory
from app.auth import RoleChecker, User
from app.schemas import (
    ResumeScreeningResponse, AssessmentGenerateResponse, AssessmentEvaluateRequest, AssessmentEvaluateResponse,
    LocationDistributionResponse, ExperienceDistributionResponse, EducationDistributionResponse,
    FunnelResponse, DiversityResponse, InterviewSlotResponse, InterviewResponse
)
from app.services.matcher import calculate_match_score

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recruitment-tools-and-analytics"])

# RBAC permissions
recruiter_manager_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])
any_auth_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin", "Candidate"])


# =====================================================================
# SECTION 5: RECRUITMENT TOOLS
# =====================================================================

# TOOL 1: Resume Screening
@router.post("/tools/resume-screening", response_model=ResumeScreeningResponse, status_code=status.HTTP_200_OK)
def tool_resume_screening(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Resume Screening Tool: Automatically screen candidate against a job.
    Evaluates experience requirements and skills overlap.
    """
    logger.info(f"Tool: Resume Screening for candidate {candidate_id} against job {job_id}")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate or Job not found.")

    cand_skills_raw = candidate.skills
    job_reqs_raw = job.requirements
    cand_skills: List[str] = cast(List[str], cand_skills_raw) if cand_skills_raw is not None else []
    job_reqs: List[str] = cast(List[str], job_reqs_raw) if job_reqs_raw is not None else []
    cand_exp = int(cast(Any, candidate.experience)) if candidate.experience is not None else 0
    job_exp = int(cast(Any, job.experience_required)) if job.experience_required is not None else 0
 
    match_score, matched_skills, missing_skills, experience_gap = calculate_match_score(
        cand_skills, job_reqs, cand_exp, job_exp
    )

    experience_check = bool(cand_exp >= job_exp)
    reasons = []
    
    if experience_check:
        reasons.append(f"Candidate meets or exceeds experience requirements ({cand_exp} yrs vs {job_exp} yrs required).")
    else:
        reasons.append(f"Candidate does not meet experience requirements (has {cand_exp} yrs but needs {job_exp} yrs).")

    skills_ratio = len(matched_skills) / len(job_reqs) if len(job_reqs) > 0 else 1.0
    skills_percent = round(skills_ratio * 100, 2)
    if skills_percent >= 50.0:
        reasons.append(f"Passed skills check: matched {skills_percent}% of required skills.")
    else:
        reasons.append(f"Failed skills check: matched only {skills_percent}% of required skills (minimum threshold is 50%).")
 
    passed_screening = bool(experience_check and (skills_percent >= 50.0))

    # Log action to candidate history
    history_action = "Resume Screened (Pass)" if passed_screening else "Resume Screened (Fail)"
    history_details = f"Screened against Job ID {job_id} ({job.title}). Score: {match_score}%. Reasons: {', '.join(reasons)}"
    
    history = CandidateHistory(
        candidate_id=candidate_id,
        action=history_action,
        details=history_details,
        performed_by=str(_current_user.username)
    )
    db.add(history)
    db.commit()

    return ResumeScreeningResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        passed_screening=passed_screening,
        experience_check=experience_check,
        skills_match_percentage=skills_percent,
        reasons=reasons
    )


# TOOL 2: Candidate Assessment
@router.post("/tools/candidate-assessment/generate", response_model=AssessmentGenerateResponse, status_code=status.HTTP_200_OK)
def tool_generate_assessment(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Candidate Assessment Tool: Generate customized coding and technical assessment questions
    based on the candidate's listed skills.
    """
    logger.info(f"Tool: Generating Assessment for candidate {candidate_id}")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    skills = candidate.skills or ["General Software Engineering"]
    assessment_questions = []
    
    # Generate assessment questions for top 3 candidate skills
    for skill in skills[:3]:
        assessment_questions.append({
            "question": f"Design a highly efficient database structure or class system implementing {skill} in a production environment. Explain the scaling constraints.",
            "category": f"{skill} Architecture",
            "difficulty": "Medium"
        })
    # Add a behavioral question
    assessment_questions.append({
        "question": "Describe a scenario where you had to debug a critical issue in production under tight deadlines. What tools and methods did you use?",
        "category": "Problem Solving",
        "difficulty": "Easy"
    })

    return AssessmentGenerateResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        test_id=f"test_{uuid.uuid4().hex[:8]}",
        assessment_questions=assessment_questions
    )

@router.post("/tools/candidate-assessment/evaluate", response_model=AssessmentEvaluateResponse, status_code=status.HTTP_200_OK)
def tool_evaluate_assessment(
    req: AssessmentEvaluateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Candidate Assessment Tool: Evaluate candidate answers and calculate test score.
    Automatically moves candidate to 'Screening' status if passed.
    """
    logger.info(f"Tool: Evaluating Assessment for candidate {req.candidate_id}")
    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    answers_count = len(req.answers)
    if answers_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No answers provided for evaluation.")

    # Calculate mock score (based on non-empty answers)
    non_empty_answers = sum(1 for a in req.answers if a.get("answer") is not None and len(str(a.get("answer")).strip()) > 20)
    score = round((non_empty_answers / answers_count) * 100, 2)
    passed = score >= 70.0

    evaluation_summary = (
        f"Candidate answered {non_empty_answers} out of {answers_count} questions thoroughly. "
        f"Total score: {score}%. Status: {'Passed' if passed else 'Failed'}."
    )

    # If passed, transition candidate to screening
    old_status = str(candidate.status)
    if passed:
        cast(Any, candidate).status = "Screening"
        
    db.commit()

    # Log history
    history = CandidateHistory(
        candidate_id=req.candidate_id,
        action="Assessment Evaluated",
        details=f"{evaluation_summary} | Status changed from {old_status} to {str(candidate.status)}",
        performed_by=str(_current_user.username)
    )
    db.add(history)
    db.commit()

    return AssessmentEvaluateResponse(
        candidate_id=req.candidate_id,
        job_id=req.job_id,
        score=score,
        passed=passed,
        evaluation_summary=evaluation_summary
    )


# TOOL 3: Interview Scheduling Tool (Alias mappings)
@router.get("/tools/interview-scheduling/slots", response_model=List[InterviewSlotResponse])
def tool_get_slots(
    db: Session = Depends(get_db),
    _current_user: User = Depends(any_auth_checker)
):
    """
    Interview Scheduling Tool: Retrieve all available slots.
    """
    return db.query(InterviewSlot).filter(InterviewSlot.is_booked == False).all()


# =====================================================================
# SECTION 6: ANALYTICS APIS
# =====================================================================

@router.get("/analytics/location-distribution", response_model=LocationDistributionResponse, status_code=status.HTTP_200_OK)
def get_location_distribution(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve candidate counts grouped by location (Case-Insensitive).
    """
    candidates = db.query(Candidate.location).all()
    dist = {}
    for c in candidates:
        loc = c[0]
        if loc:
            loc_clean = loc.strip().title()
            dist[loc_clean] = dist.get(loc_clean, 0) + 1
        else:
            dist["Not Specified"] = dist.get("Not Specified", 0) + 1
            
    return LocationDistributionResponse(location_distribution=dist)


@router.get("/analytics/experience-distribution", response_model=ExperienceDistributionResponse, status_code=status.HTTP_200_OK)
def get_experience_distribution(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve candidate counts grouped by experience range (Entry, Mid, Senior, Lead).
    """
    candidates = db.query(Candidate.experience).all()
    dist = {
        "Entry Level (0-2 yrs)": 0,
        "Mid Level (3-5 yrs)": 0,
        "Senior Level (6-10 yrs)": 0,
        "Lead/Director (10+ yrs)": 0
    }
    for c in candidates:
        exp = c[0] or 0
        if exp <= 2:
            dist["Entry Level (0-2 yrs)"] += 1
        elif exp <= 5:
            dist["Mid Level (3-5 yrs)"] += 1
        elif exp <= 10:
            dist["Senior Level (6-10 yrs)"] += 1
        else:
            dist["Lead/Director (10+ yrs)"] += 1
            
    return ExperienceDistributionResponse(experience_distribution=dist)


@router.get("/analytics/education-distribution", response_model=EducationDistributionResponse, status_code=status.HTTP_200_OK)
def get_education_distribution(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve candidate counts grouped by education degree/level.
    """
    candidates = db.query(Candidate.education).all()
    dist = {
        "Ph.D. / Doctorates": 0,
        "Master's Degree": 0,
        "Bachelor's Degree": 0,
        "Diploma / Others": 0
    }
    for c in candidates:
        edu = (c[0] or "").lower()
        if not edu:
            dist["Diploma / Others"] += 1
        elif "ph.d" in edu or "doctor" in edu:
            dist["Ph.D. / Doctorates"] += 1
        elif any(kw in edu for kw in ["master", "m.tech", "m.e", "mba", "mca", "m.sc"]):
            dist["Master's Degree"] += 1
        elif any(kw in edu for kw in ["b.tech", "b.e", "bachelor", "b.sc", "bca", "bba"]):
            dist["Bachelor's Degree"] += 1
        else:
            dist["Diploma / Others"] += 1
            
    return EducationDistributionResponse(education_distribution=dist)


@router.get("/analytics/hiring-funnel", response_model=FunnelResponse, status_code=status.HTTP_200_OK)
def get_hiring_funnel_distribution(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve candidate hiring funnel distribution showing counts at each stage.
    """
    status_counts_raw = db.query(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status).all()
    status_counts = {s[0]: s[1] for s in status_counts_raw}
    
    funnel = {
        "Applied": status_counts.get("Applied", 0) + status_counts.get("Parsed", 0) + status_counts.get("Matched", 0),
        "Screening": status_counts.get("Screening", 0),
        "Shortlisted": status_counts.get("Shortlisted", 0),
        "Interview Scheduled": status_counts.get("Interview Scheduled", 0) + status_counts.get("Interview", 0),
        "Selected": status_counts.get("Selected", 0),
        "Rejected": status_counts.get("Rejected", 0)
    }
    
    return FunnelResponse(hiring_funnel=funnel)


@router.get("/analytics/diversity-analytics", response_model=DiversityResponse, status_code=status.HTTP_200_OK)
def get_diversity_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Retrieve estimated diversity metrics: Gender distribution (estimated by name/pronouns)
    and top hiring university distribution.
    """
    candidates = db.query(Candidate.name, Candidate.education, Candidate.resume_text).all()
    
    gender_dist = {"Male": 0, "Female": 0, "Not Specified": 0}
    university_counts = {}

    female_names = ["alice", "jane", "emma", "sophia", "olivia", "priya", "neha", "pooja", "anjali", "divya", "aishwarya", "sneha", "kirti", "ritu", "anita"]
    male_names = ["bob", "rahul", "john", "michael", "david", "james", "amit", "rohit", "vijay", "ajay", "vikram", "rajesh", "suresh", "ayush", "sanjay", "deep"]

    for name, edu, resume in candidates:
        # 1. Estimate Gender
        first_name = name.split()[0].lower() if name else ""
        gender = "Not Specified"
        
        if first_name in female_names:
            gender = "Female"
        elif first_name in male_names:
            gender = "Male"
        else:
            # Check pronouns in resume text as secondary indicator
            res_text = (resume or "").lower()
            she_count = res_text.count("she ") + res_text.count("her ")
            he_count = res_text.count("he ") + res_text.count("him ")
            
            if she_count > he_count:
                gender = "Female"
            elif he_count > she_count:
                gender = "Male"
                
        gender_dist[gender] += 1

        # 2. Estimate University
        if edu:
            edu_lower = edu.lower()
            # Simple university keywords
            found_univ = False
            for univ_kw in ["iit", "nit", "stanford", "mit", "bits", "pune university", "mumbai university", "delhi university", "harvard"]:
                if univ_kw in edu_lower:
                    univ_name = univ_kw.upper() if len(univ_kw) <= 4 else univ_kw.title()
                    university_counts[univ_name] = university_counts.get(univ_name, 0) + 1
                    found_univ = True
                    break
            if not found_univ:
                university_counts["Other Universities"] = university_counts.get("Other Universities", 0) + 1
        else:
            university_counts["Not Specified"] = university_counts.get("Not Specified", 0) + 1

    # Get top 5 universities
    sorted_universities = sorted(university_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_universities = {k: v for k, v in sorted_universities}

    return DiversityResponse(
        gender_distribution=gender_dist,
        university_distribution=top_universities
    )
