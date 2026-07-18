RESUME_PROMPT = """
You are an AI Recruiter.

Extract the following information from the resume.

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