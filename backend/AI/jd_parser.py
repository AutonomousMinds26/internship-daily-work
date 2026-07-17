import re


def extract_job_info(job_text):

    job = {
        "job_title": "",
        "required_skills": [],
        "experience": "",
        "location": "",
        "salary_range": "",
        "notice_period": ""
    }

    # -------- Job Title --------
    lines = job_text.split("\n")

    for line in lines:
        line = line.strip()

        if len(line) > 3:
            job["job_title"] = line
            break

    # -------- Skills --------
    skills_database = [
        "Python",
        "Java",
        "React",
        "FastAPI",
        "SQL",
        "AWS",
        "Docker",
        "Git",
        "Machine Learning",
        "LangChain",
        "TensorFlow",
        "Pandas",
        "NumPy",
        "JavaScript"
    ]

    for skill in skills_database:
        if skill.lower() in job_text.lower():
            job["required_skills"].append(skill)

    # -------- Experience --------
    exp = re.search(r'(\d+\+?\s*years?)', job_text, re.IGNORECASE)

    if exp:
        job["experience"] = exp.group()

    # -------- Salary --------
    salary = re.search(r'(\d+\s*-\s*\d+\s*LPA)', job_text, re.IGNORECASE)

    if salary:
        job["salary_range"] = salary.group()

    # -------- Notice Period --------
    notice = re.search(r'(\d+\s*Days)', job_text, re.IGNORECASE)

    if notice:
        job["notice_period"] = notice.group()

    # -------- Location --------
    cities = [
        "Pune",
        "Mumbai",
        "Bangalore",
        "Bengaluru",
        "Delhi",
        "Hyderabad",
        "Chennai"
    ]

    for city in cities:
        if city.lower() in job_text.lower():
            job["location"] = city
            break

    return job

if __name__ == "__main__":

    import os
    import json

    path = os.path.abspath("backend/AI/sample_job.txt")
    print("Reading from:", path)

    with open(path, "r", encoding="utf-8") as file:
        job_text = file.read()

    print("Characters read:", len(job_text))

    print("\n===== JOB TEXT =====")
    print(job_text)
    print("====================\n")

    job = extract_job_info(job_text)

    print(json.dumps(job, indent=4))