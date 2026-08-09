import json
import logging
import re
import math
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from AI.llm import llm
except ImportError:
    try:
        from llm import llm
    except ImportError:
        llm = None

# --- Prompt for ATS Analysis ---
ATS_ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) Scanner.

Analyze the candidate's resume/profile details against the Job Description (JD) requirements.
Evaluate the following:
1. Resume-JD relevance (overall matching of candidate context to job context)
2. Required skill coverage (what percent of job required skills are present in the candidate's skills list/resume)
3. Experience match (how well candidate's years of experience and experience description align with job requirements)
4. Education match (education requirements met)
5. Project relevance (how relevant candidate's projects are to the job description/role)
6. Keyword coverage (standard ATS keyword matching, focusing on key technologies and terminologies in JD)
7. Resume completeness (check if essential sections: summary, experience, education, projects, skills are all present)
8. Missing important sections (identify if any standard section like projects, certifications, summary, etc. is missing)
9. Contact information completeness (check if name, email, phone, and professional links like LinkedIn are present)
10. Job-specific terminology (check if job-specific industry terms, tools, or frameworks are utilized in the resume)

Return ONLY valid JSON. Do not include markdown styling, "```json" wrappers, or text outside the JSON.

Expected output format:
{{
    "ats_score": 91,
    "keyword_match": 94,
    "skill_match": 100,
    "experience_match": 90,
    "education_match": 100,
    "resume_completeness": 95,
    "issues": [
        "No LinkedIn profile detected"
    ],
    "recommendation": "ATS Friendly"
}}

Candidate Profile:
{candidate}

Job Description:
{job}
"""

def extract_years_numeric(text) -> int:
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

def clean_json_response(content: str) -> str:
    content = content.strip()
    content = re.sub(r"^```(?:json)?", "", content)
    content = re.sub(r"```$", "", content)
    return content.strip()

def analyze_ats(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans and scores a candidate resume/profile against job details for ATS compatibility.
    Integrates ChatGroq LLM evaluation, falling back to a pure-Python matching logic if needed.
    """
    if llm is not None:
        try:
            cand_str = json.dumps(candidate, indent=2)
            job_str = json.dumps(job, indent=2)
            prompt = ATS_ANALYSIS_PROMPT.format(candidate=cand_str, job=job_str)
            
            logger.info("Invoking LLM for ATS scoring analysis...")
            response = llm.invoke(prompt)
            content = clean_json_response(str(response.content))
            
            result = json.loads(content)
            # Ensure correct format
            return {
                "ats_score": int(result.get("ats_score", 0)),
                "keyword_match": int(result.get("keyword_match", 0)),
                "skill_match": int(result.get("skill_match", 0)),
                "experience_match": int(result.get("experience_match", 0)),
                "education_match": int(result.get("education_match", 0)),
                "resume_completeness": int(result.get("resume_completeness", 0)),
                "issues": list(result.get("issues", [])),
                "recommendation": str(result.get("recommendation", "Needs Review"))
            }
        except Exception as e:
            logger.error(f"LLM ATS scanner failed: {str(e)}. Using python fallback scanner.")

    # --- Pure-Python Fallback Scanner ---
    return analyze_ats_fallback(candidate, job)

def analyze_ats_fallback(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    
    # 1. Resume Completeness (check essential sections)
    completeness_score = 0
    total_sections = 6
    if candidate.get("name") and candidate["name"] != "Unknown Candidate":
        completeness_score += 1
    else:
        issues.append("Candidate name is missing or unknown")
        
    if candidate.get("email") and "@" in candidate["email"]:
        completeness_score += 1
    else:
        issues.append("Valid email address is missing")
        
    if candidate.get("phone"):
        completeness_score += 1
    else:
        issues.append("Contact phone number is missing")
        
    skills = candidate.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if skills:
        completeness_score += 1
    else:
        issues.append("Skills section is empty")
        
    education = candidate.get("education", "")
    if education and education != "Not Specified" and education != "Not Available":
        completeness_score += 1
    else:
        issues.append("Education history is missing")
        
    projects = candidate.get("projects", [])
    if isinstance(projects, str):
        projects = [p.strip() for p in projects.split(",") if p.strip()]
    if projects:
        completeness_score += 1
    else:
        issues.append("Projects section is missing")
        
    resume_completeness = int((completeness_score / total_sections) * 100)
    
    # Check LinkedIn/GitHub in resume text or fields
    resume_text = str(candidate.get("resume_text", "")).lower()
    if "linkedin.com" not in resume_text and "linkedin" not in resume_text:
        issues.append("No LinkedIn profile detected")
    if "github.com" not in resume_text and "github" not in resume_text:
        issues.append("No GitHub profile detected")

    # 2. Skill Match
    job_skills = job.get("required_skills", [])
    if isinstance(job_skills, str):
        job_skills = [s.strip() for s in job_skills.split(",") if s.strip()]
    
    cand_skills_norm = {s.lower().strip() for s in skills}
    job_skills_norm = {s.lower().strip() for s in job_skills}
    
    matched_skills = cand_skills_norm & job_skills_norm
    if job_skills_norm:
        skill_match = int((len(matched_skills) / len(job_skills_norm)) * 100)
    else:
        skill_match = 100
        
    if len(job_skills_norm - cand_skills_norm) > 0:
        missing_skills_str = ", ".join(list(job_skills_norm - cand_skills_norm)[:3])
        issues.append(f"Missing core skills requested: {missing_skills_str}")

    # 3. Experience Match
    cand_exp = extract_years_numeric(candidate.get("experience", 0))
    job_exp = extract_years_numeric(job.get("experience", 0))
    if job_exp <= 0:
        experience_match = 100
    else:
        experience_match = min(100, int((cand_exp / job_exp) * 100))
        
    if cand_exp < job_exp:
        issues.append(f"Candidate experience ({cand_exp} yrs) is less than required ({job_exp} yrs)")

    # 4. Education Match
    education_match = 100
    edu_text = str(candidate.get("education", "")).lower()
    job_desc = str(job.get("description", "")).lower()
    
    # Check if master/phd mentioned in job desc but missing in education
    if "master" in job_desc or "m.tech" in job_desc or "mba" in job_desc:
        if not any(kw in edu_text for kw in ["master", "m.tech", "mba", "m.e", "m.sc", "mca"]):
            education_match = 70
            issues.append("Job description requests higher degree (Master/MBA), candidate lists Bachelor or lower")
    if "ph.d" in job_desc or "phd" in job_desc or "doctor" in job_desc:
        if not any(kw in edu_text for kw in ["ph.d", "phd", "doctor"]):
            education_match = 50
            issues.append("Job description requests Doctorate/PhD, candidate education level does not match")

    # 5. Keyword Match (Jaccard similarity of vocabulary words)
    def get_tokens(text: str) -> List[str]:
        return re.findall(r'\b\w{3,}\b', text.lower()) # words of length >= 3
        
    cand_tokens = set(get_tokens(resume_text + " " + " ".join(skills)))
    job_text = str(job.get("description", "")) + " " + " ".join(job_skills)
    job_tokens = set(get_tokens(job_text))
    
    intersect = cand_tokens & job_tokens
    union = cand_tokens | job_tokens
    
    if union:
        # Scale Jaccard similarity to score between 30 and 100 for better realism
        jaccard = len(intersect) / len(job_tokens) if job_tokens else 0.0
        keyword_match = min(100, int(30 + (jaccard * 70)))
    else:
        keyword_match = 100

    # 6. Overall ATS Score (weighted average)
    ats_score = int(
        (0.25 * resume_completeness) + 
        (0.25 * skill_match) + 
        (0.20 * experience_match) + 
        (0.15 * education_match) + 
        (0.15 * keyword_match)
    )
    
    if ats_score >= 80:
        recommendation = "ATS Friendly"
    elif ats_score >= 50:
        recommendation = "Needs Improvement"
    else:
        recommendation = "Not ATS Friendly"

    return {
        "ats_score": ats_score,
        "keyword_match": keyword_match,
        "skill_match": skill_match,
        "experience_match": experience_match,
        "education_match": education_match,
        "resume_completeness": resume_completeness,
        "issues": issues,
        "recommendation": recommendation
    }

