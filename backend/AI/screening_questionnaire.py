import json
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from AI.llm import llm
except ImportError:
    try:
        from llm import llm
    except ImportError:
        llm = None

SCREENING_QUESTIONNAIRE_PROMPT = """
You are an AI Recruitment Assistant. Your task is to generate a screening questionnaire for a candidate applying to a job.
The questionnaire must contain questions from the following categories:
- Technical Questions (focused on candidate's technical skills and job requirements)
- Experience Questions (focused on candidate's experience and background)
- Availability Questions (focused on notice period, start date)
- Salary Questions (expected salary/CTC)
- Location Questions (location alignment, willingness to relocate)

Return ONLY valid JSON. Do not include markdown styling, "```json" wrappers, or text outside the JSON.

Expected output format:
{{
    "technical_questions": [
        "Explain your FastAPI experience."
    ],
    "experience_questions": [
        "How many years of Python experience do you have?"
    ],
    "availability_questions": [
        "What is your current notice period?"
    ],
    "salary_questions": [
        "What is your expected CTC?"
    ],
    "location_questions": [
        "Are you comfortable working from Pune?",
        "Are you willing to relocate if required?"
    ]
}}

Candidate Profile:
{candidate}

Job Description:
{job}
"""

def clean_json_response(content: str) -> str:
    content = content.strip()
    content = re.sub(r"^```(?:json)?", "", content)
    content = re.sub(r"```$", "", content)
    return content.strip()

def generate_screening_questionnaire(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a structured screening questionnaire tailored to the candidate and job requirements.
    Integrates ChatGroq LLM, falling back to pure-Python heuristics if needed.
    """
    if llm is not None:
        try:
            cand_str = json.dumps(candidate, indent=2)
            job_str = json.dumps(job, indent=2)
            prompt = SCREENING_QUESTIONNAIRE_PROMPT.format(candidate=cand_str, job=job_str)
            
            logger.info("Invoking LLM for screening questionnaire generation...")
            response = llm.invoke(prompt)
            content = clean_json_response(str(response.content))
            
            result = json.loads(content)
            # Ensure correct format
            return {
                "technical_questions": list(result.get("technical_questions", [])),
                "experience_questions": list(result.get("experience_questions", [])),
                "availability_questions": list(result.get("availability_questions", [])),
                "salary_questions": list(result.get("salary_questions", [])),
                "location_questions": list(result.get("location_questions", []))
            }
        except Exception as e:
            logger.error(f"LLM screening questionnaire generator failed: {str(e)}. Using fallback.")

    # --- Pure-Python Fallback ---
    return generate_screening_questionnaire_fallback(candidate, job)

def generate_screening_questionnaire_fallback(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    job_title = job.get("job_title", "the role")
    job_loc = job.get("location", "the designated office")
    
    # 1. Technical questions
    tech_qs = []
    cand_skills = candidate.get("skills", [])
    if isinstance(cand_skills, str):
        cand_skills = [s.strip() for s in cand_skills.split(",") if s.strip()]
        
    job_skills = job.get("required_skills", [])
    if isinstance(job_skills, str):
        job_skills = [s.strip() for s in job_skills.split(",") if s.strip()]
        
    matched_skills = [s for s in cand_skills if s.lower() in [js.lower() for js in job_skills]]
    missing_skills = [s for s in job_skills if s.lower() not in [cs.lower() for cs in cand_skills]]
    
    if matched_skills:
        tech_qs.append(f"Explain your experience working with {matched_skills[0]}.")
    if missing_skills:
        tech_qs.append(f"Have you worked with {missing_skills[0]} before, or any similar tool/technology?")
    if not tech_qs:
        tech_qs.append(f"Describe a complex technical challenge you solved recently.")

    # 2. Experience questions
    exp_qs = []
    job_exp = job.get("experience", 0)
    exp_qs.append(f"How many years of professional experience do you have in software engineering?")
    exp_qs.append(f"Describe your roles and responsibilities in your most recent project.")

    # 3. Availability questions
    avail_qs = [
        "What is your current notice period?",
        "When is the earliest you can join us if selected?"
    ]

    # 4. Salary questions
    sal_qs = [
        "What is your expected CTC/salary?",
        "Are you open to negotiation on compensation?"
    ]

    # 5. Location questions
    loc_qs = []
    if job_loc and job_loc != "Remote":
        loc_qs.append(f"Are you comfortable working from {job_loc}?")
        loc_qs.append(f"Are you willing to relocate to {job_loc} if required?")
    else:
        loc_qs.append("Are you comfortable working in a fully remote or hybrid setup?")

    return {
        "technical_questions": tech_qs,
        "experience_questions": exp_qs,
        "availability_questions": avail_qs,
        "salary_questions": sal_qs,
        "location_questions": loc_qs
    }
