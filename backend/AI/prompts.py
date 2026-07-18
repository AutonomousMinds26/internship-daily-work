RESUME_PROMPT = """
You are an AI Resume Parser.

Extract the following information.

Return ONLY valid JSON.

{{
    "name": "",
    "email": "",
    "phone": "",
    "education": "",
    "experience": "",
    "skills": [],
    "projects": [],
    "notice_period": "",
    "expected_ctc": "",
    "location": ""
}}

Resume:

{text}
"""


JOB_PROMPT = """
You are an AI Job Description Parser.

Extract the following information.

Return ONLY valid JSON.

{{
    "job_title": "",
    "required_skills": [],
    "experience": "",
    "location": "",
    "salary_range": "",
    "notice_period": ""
}}

Job Description:

{text}
"""


AI_SCORE_PROMPT = """
You are an expert Technical Recruiter.

Compare the candidate profile with the Job Description.

Evaluate:

- Skills
- Projects
- Experience
- Education
- Location
- Notice Period
- Overall Fit

Return ONLY valid JSON.

{{
    "match_percentage": 0,
    "matched_skills": [],
    "missing_skills": [],
    "strengths": [],
    "weaknesses": [],
    "recommendation": ""
}}

Candidate

{candidate}

Job Description

{job}
"""