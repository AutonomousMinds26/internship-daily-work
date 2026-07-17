import fitz
import json

from extractor import extract_candidate_info
from jd_parser import extract_job_info


# -----------------------------------
# Read Resume PDF
# -----------------------------------
def extract_resume_text(file_path):

    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


# -----------------------------------
# Calculate Candidate Score
# -----------------------------------
def calculate_score(candidate, job):

    # Convert skills to lowercase for comparison
    candidate_skills = {skill.lower(): skill for skill in candidate["skills"]}
    required_skills = {skill.lower(): skill for skill in job["required_skills"]}

    # Matching skills
    matched_keys = set(candidate_skills.keys()).intersection(required_skills.keys())

    matched_skills = [candidate_skills[key] for key in matched_keys]

    # Missing skills
    missing_skills = [
        required_skills[key]
        for key in required_skills.keys()
        if key not in matched_keys
    ]

    # Score calculation
    if len(required_skills) == 0:
        score = 0
    else:
        score = round((len(matched_skills) / len(required_skills)) * 100)

    # Recommendation
    if score >= 80:
        recommendation = "Shortlist"
    elif score >= 50:
        recommendation = "Maybe"
    else:
        recommendation = "Reject"

    return {
        "candidate": candidate["name"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": score,
        "recommendation": recommendation
    }


# -----------------------------------
# Main
# -----------------------------------
if __name__ == "__main__":

    # Read Resume
    resume_path = "sample_resumes/sample4.pdf"

    resume_text = extract_resume_text(resume_path)

    candidate = extract_candidate_info(resume_text)

    # Read Job Description
    with open("backend/AI/sample_job.txt", "r", encoding="utf-8") as file:
        job_text = file.read()

    job = extract_job_info(job_text)

    # Calculate Score
    result = calculate_score(candidate, job)

    print("\n========== CANDIDATE SCORE ==========\n")

    print(json.dumps(result, indent=4))