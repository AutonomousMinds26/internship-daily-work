import re

def extract_experience(text: str) -> int:
    """
    Tries to extract years of experience from text using simple regex.
    """
    # Pattern: 3+ years of experience, 5 years experience
    match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern: experience: 4 years
    match = re.search(r'experience\s*:\s*(\d+)\+?\s*(?:years?|yrs?)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern: 5+ Yrs
    match = re.search(r'(\d+)\+?\s*yrs\b', text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return 0

def extract_education(text: str) -> str:
    """
    Tries to extract degrees or education level from text.
    """
    degrees = ["B.Tech", "B.E.", "M.Tech", "M.E.", "M.S.", "B.S.", "Ph.D", "B.C.A", "M.C.A", "Bachelor", "Master", "Degree"]
    found_degrees = []
    for degree in degrees:
        # Match word boundaries or dots
        pattern = rf'\b{re.escape(degree)}\b'
        if degree.endswith('.'): # e.g. B.E.
            pattern = rf'{re.escape(degree)}'
        if re.search(pattern, text, re.IGNORECASE):
            found_degrees.append(degree)
    
    if found_degrees:
        return ", ".join(found_degrees)
    
    # Fallback to check common keywords
    if "university" in text.lower() or "college" in text.lower():
        return "Degree Details in Resume"
        
    return "Not Specified"

def extract_candidate_info(text: str) -> dict:
    candidate = {
        "name": "",
        "email": "",
        "phone": "",
        "education": "",
        "experience": 0,
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
        if len(line) > 2 and not any(kwd in line.lower() for kwd in ["resume", "cv", "page", "email", "phone"]):
            candidate["name"] = line
            break
    if not candidate["name"]:
        candidate["name"] = "Unknown Candidate"

    # ---------- Experience ----------
    candidate["experience"] = extract_experience(text)

    # ---------- Education ----------
    candidate["education"] = extract_education(text)

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
        "Git",
        "PostgreSQL",
        "Redis"
    ]

    for skill in skill_database:
        # Check skill using case-insensitive word-boundary
        pattern = rf'\b{re.escape(skill.lower())}\b'
        if skill == "C++":
            pattern = r'c\+\+'
        if re.search(pattern, text.lower()):
            candidate["skills"].append(skill)

    # ---------- Location, Notice, CTC ----------
    loc_match = re.search(r'location\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if loc_match:
        candidate["location"] = loc_match.group(1).strip()
        
    notice_match = re.search(r'notice\s*period\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if notice_match:
        candidate["notice_period"] = notice_match.group(1).strip()
        
    ctc_match = re.search(r'expected\s*ctc\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if ctc_match:
        candidate["expected_ctc"] = ctc_match.group(1).strip()

    return candidate
