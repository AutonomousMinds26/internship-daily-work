from typing import List, Tuple

def calculate_match_score(
    candidate_skills: List[str],
    job_requirements: List[str],
    cand_exp: int,
    job_exp_req: int
) -> Tuple[float, List[str], List[str], int]:
    """
    Computes a match score out of 100.
    Weighting:
    - 60%: Skills Match (percentage of job requirements matched)
    - 40%: Experience Match (candidate experience vs required)
    
    Returns:
        (match_score, matched_skills, missing_skills, experience_gap)
    """
    # Case insensitive comparison helpers
    cand_skills_lower = {s.lower().strip() for s in candidate_skills if s}
    
    matched_skills = []
    missing_skills = []
    
    for req in job_requirements:
        req_clean = req.strip()
        if not req_clean:
            continue
        if req_clean.lower() in cand_skills_lower:
            matched_skills.append(req_clean)
        else:
            missing_skills.append(req_clean)
            
    # Calculate skills match score
    if not job_requirements:
        skills_score = 100.0
    else:
        total_reqs = len(job_requirements)
        skills_score = (len(matched_skills) / total_reqs) * 100.0
        
    # Calculate experience score and gap
    experience_gap = max(0, job_exp_req - cand_exp)
    if job_exp_req <= 0:
        experience_score = 100.0
    else:
        # Scale score: candidate experience as a ratio of required
        ratio = cand_exp / job_exp_req
        experience_score = min(100.0, ratio * 100.0)
        
    # Final weighted score
    match_score = (0.6 * skills_score) + (0.4 * experience_score)
    
    return round(match_score, 2), matched_skills, missing_skills, experience_gap
