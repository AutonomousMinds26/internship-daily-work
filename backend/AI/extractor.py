import re


def extract_candidate_info(text):

    candidate = {
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
    }

    # ---------- Email ----------
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)

    if email:
        candidate["email"] = email.group()

    # ---------- Phone ----------
    phone = re.search(r'(\+91[- ]?)?[6-9]\d{9}', text)

    if phone:
        candidate["phone"] = phone.group()

    # ---------- Name ----------
    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        if len(line) > 2:
            candidate["name"] = line
            break

    # ---------- Skills ----------
    skill_database = [
        "Python",
        "Java",
        "C++",
        "SQL",
        "AWS",
        "FastAPI",
        "React",
        "JavaScript",
        "Machine Learning",
        "LangChain",
        "TensorFlow",
        "Pandas",
        "NumPy",
        "Docker",
        "Git"
    ]

    for skill in skill_database:

        if skill.lower() in text.lower():
            candidate["skills"].append(skill)

    return candidate