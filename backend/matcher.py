def calculate_skill_match(candidate_skills_str: str, job_skills_str: str) -> float:
    """
    Compares candidate's skills and job's required skills.
    Skills are passed as comma-separated strings.
    """
    if not job_skills_str:
        return 100.0
    if not candidate_skills_str:
        return 0.0

    # Parse and clean skills
    cand_skills = {s.strip().lower() for s in candidate_skills_str.split(",") if s.strip()}
    job_skills = {s.strip().lower() for s in job_skills_str.split(",") if s.strip()}

    if not job_skills:
        return 100.0

    # Calculate overlap
    matched_skills = cand_skills.intersection(job_skills)
    match_percentage = (len(matched_skills) / len(job_skills)) * 100
    return round(match_percentage, 2)

def get_matching_recommendation(match_percentage: float) -> str:
    """
    Determines recommendation based on match percentage.
    """
    if match_percentage >= 70.0:
        return "Shortlist"
    elif match_percentage >= 40.0:
        return "Under Review"
    else:
        return "Reject"

def match_candidate_to_job(candidate, job) -> dict:
    """
    Matches candidate against a job record.
    """
    match_percentage = calculate_skill_match(candidate.skills, job.required_skills)
    recommendation = get_matching_recommendation(match_percentage)

    return {
        "candidate_name": candidate.name,
        "skill_match": f"{match_percentage}%",
        "recommendation": recommendation
    }
