import re
import logging

logger = logging.getLogger(__name__)

def extract_years(text):
    if not text:
        return 0
    if isinstance(text, (int, float)):
        return int(text)
    text = str(text).lower()
    match = re.search(r'(\d+)\+?\s*(years|year|yrs)', text)
    if match:
        return int(match.group(1))
    match_any = re.search(r'(\d+)', text)
    if match_any:
        return int(match_any.group(1))
    return 0

def normalize(text):
    if not text:
        return ""
    return str(text).lower().strip()

def calculate_score(candidate, job):
    """Fallback standard legacy scorer method (calls calculate_enhanced_score internally)."""
    return calculate_enhanced_score(candidate, job)

def calculate_enhanced_score(candidate: dict, job: dict) -> dict:
    """
    Enhanced Candidate Scoring Algorithm (11 criteria):
    1. Skills Match (30 pts)
    2. Experience Match (15 pts)
    3. Education Alignment (10 pts)
    4. Projects (10 pts)
    5. Certifications (5 pts)
    6. Achievements (5 pts)
    7. Languages (5 pts)
    8. Soft Skills (5 pts)
    9. Expected Salary (5 pts)
    10. Current Company (5 pts)
    11. Employment Gap Check (5 pts)
    Total = 100 points
    """
    # 1. Skills Score (30%)
    cand_skills = {normalize(s) for s in candidate.get("skills", []) if s}
    job_reqs = {normalize(s) for s in job.get("required_skills", []) if s}
    matched_skills = cand_skills & job_reqs
    missing_skills = job_reqs - cand_skills
    
    if job_reqs:
        skills_score = (len(matched_skills) / len(job_reqs)) * 30
    else:
        skills_score = 30.0

    # 2. Experience Score (15%)
    cand_exp = extract_years(candidate.get("experience", 0))
    job_exp = extract_years(job.get("experience", 0))
    if job_exp <= 0:
        experience_score = 15.0
    else:
        experience_score = min(15.0, (cand_exp / job_exp) * 15)

    # 3. Education Score (10%)
    edu_text = normalize(candidate.get("education", ""))
    education_score = 5.0
    if "ph.d" in edu_text or "doctor" in edu_text:
        education_score = 10.0
    elif any(kw in edu_text for kw in ["master", "m.tech", "m.e", "mba", "mca", "m.sc"]):
        education_score = 9.0
    elif any(kw in edu_text for kw in ["b.tech", "b.e", "bachelor", "b.sc", "bca", "bba"]):
        education_score = 8.0

    # 4. Projects Score (10%)
    projects = candidate.get("projects", [])
    if isinstance(projects, str):
        projects = [p.strip() for p in projects.split(",") if p.strip()]
    if projects:
        project_score = min(10.0, len(projects) * 3.33)
    else:
        project_score = 0.0

    # 5. Certifications Score (5%)
    certs = candidate.get("certifications", [])
    if isinstance(certs, str):
        certs = [c.strip() for c in certs.split(",") if c.strip()]
    certification_score = 5.0 if certs else 0.0

    # 6. Achievements Score (5%)
    achievements = candidate.get("achievements", [])
    if isinstance(achievements, str):
        achievements = [a.strip() for a in achievements.split(",") if a.strip()]
    achievements_score = 5.0 if achievements else 0.0

    # 7. Languages Score (5%)
    langs = candidate.get("languages", [])
    if isinstance(langs, str):
        langs = [l.strip() for l in langs.split(",") if l.strip()]
    languages_score = 5.0 if len(langs) >= 2 else (3.0 if langs else 0.0)

    # 8. Soft Skills Score (5%)
    soft_skills = candidate.get("soft_skills", [])
    if isinstance(soft_skills, str):
        soft_skills = [s.strip() for s in soft_skills.split(",") if s.strip()]
    soft_skills_score = 5.0 if len(soft_skills) >= 2 else (3.0 if soft_skills else 0.0)

    # 9. Expected Salary Score (5%)
    expected_salary = normalize(candidate.get("expected_ctc", ""))
    salary_score = 5.0
    # simple heuristic: check if candidate expects more than salary_range
    try:
        cand_sal_match = re.search(r'(\d+)', expected_salary)
        if cand_sal_match:
            cand_sal_num = int(cand_sal_match.group(1))
            job_salary = normalize(job.get("salary_range", ""))
            job_sal_nums = [int(n) for n in re.findall(r'(\d+)', job_salary)]
            if job_sal_nums and cand_sal_num > max(job_sal_nums):
                salary_score = 2.0
    except Exception:
        pass

    # 10. Current Company Score (5%)
    curr_company = candidate.get("current_company", "")
    current_company_score = 5.0 if curr_company and curr_company != "Not Available" else 2.0

    # 11. Employment Gap Score (5%)
    has_gap = candidate.get("employment_gap", False)
    employment_gap_score = 2.0 if has_gap else 5.0

    # Sum all scores
    total_score = round(
        skills_score + experience_score + education_score + project_score +
        certification_score + achievements_score + languages_score + soft_skills_score +
        salary_score + current_company_score + employment_gap_score,
        2
    )

    # Make recommendation fit
    if total_score >= 80:
        recommendation = "Shortlist"
    elif total_score >= 50:
        recommendation = "Maybe"
    else:
        recommendation = "Reject"

    return {
        "candidate": candidate.get("name"),
        "email": candidate.get("email"),
        "match_percentage": total_score,
        "recommendation": recommendation,
        "skills_score": round(skills_score, 2),
        "experience_score": round(experience_score, 2),
        "education_score": round(education_score, 2),
        "project_score": round(project_score, 2),
        "certification_score": round(certification_score, 2),
        "achievements_score": round(achievements_score, 2),
        "languages_score": round(languages_score, 2),
        "soft_skills_score": round(soft_skills_score, 2),
        "salary_score": round(salary_score, 2),
        "current_company_score": round(current_company_score, 2),
        "employment_gap_score": round(employment_gap_score, 2),
        "matched_skills": list(matched_skills),
        "missing_skills": [s for s in job.get("required_skills", []) if normalize(s) in missing_skills]
    }