import re


def extract_years(text):

    if not text:
        return 0

    text = text.lower()

    match = re.search(
        r'(\d+)\+?\s*(years|year|yrs)',
        text
    )

    if match:
        return int(match.group(1))

    return 0



def normalize(text):

    if not text:
        return ""

    return text.lower()



def calculate_score(candidate, job):


    # ----------------------------
    # Skills Score (70%)
    # ----------------------------

    candidate_skills = {
        normalize(skill)
        for skill in candidate.get(
            "skills",
            []
        )
    }


    required_skills = {
        normalize(skill)
        for skill in job.get(
            "required_skills",
            []
        )
    }


    matched_skills = list(
        candidate_skills &
        required_skills
    )


    missing_skills = list(
        required_skills -
        candidate_skills
    )


    if required_skills:

        skill_score = (
            len(matched_skills)
            /
            len(required_skills)
        ) * 70

    else:

        skill_score = 0



    # ----------------------------
    # Experience Score (20%)
    # ----------------------------

    candidate_exp = extract_years(
        candidate.get(
            "experience",
            ""
        )
    )


    required_exp = extract_years(
        job.get(
            "experience",
            ""
        )
    )


    experience_match = (
        candidate_exp >= required_exp
    )


    experience_score = (
        20
        if experience_match
        else 0
    )



    # ----------------------------
    # Location Score (5%)
    # ----------------------------

    candidate_location = normalize(
        candidate.get(
            "location",
            ""
        )
    )


    job_location = normalize(
        job.get(
            "location",
            ""
        )
    )


    location_match = (
        job_location in candidate_location
    )


    location_score = (
        5
        if location_match
        else 0
    )



    # ----------------------------
    # Notice Period Score (5%)
    # ----------------------------

    candidate_notice = normalize(
        candidate.get(
            "notice_period",
            ""
        )
    )


    job_notice = normalize(
        job.get(
            "notice_period",
            ""
        )
    )


    notice_match = (
        job_notice in candidate_notice
        or
        candidate_notice in job_notice
    )


    notice_score = (
        5
        if notice_match
        else 0
    )



    # ----------------------------
    # Final Score
    # ----------------------------

    final_score = round(
        skill_score
        +
        experience_score
        +
        location_score
        +
        notice_score
    )


    if final_score >= 80:

        recommendation = "Shortlist"

    elif final_score >= 50:

        recommendation = "Maybe"

    else:

        recommendation = "Reject"



    return {

    "candidate":
        candidate.get("name"),

    "email":
        candidate.get("email"),

    "match_percentage":
        final_score,

    "matched_skills":
        matched_skills,

    "missing_skills":
        missing_skills,

    "recommendation":
        recommendation
}