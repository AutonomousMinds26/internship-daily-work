import os
import sys
import re
import json
import logging
from typing import Dict, Any, List, Union, Optional

# Ensure both backend and AI directories are in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ai_dir = os.path.abspath(os.path.dirname(__file__))
for p in [backend_dir, ai_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

logger = logging.getLogger(__name__)

# Optional LLM integration with safe fallback
try:
    from AI.llm import llm
except ImportError:
    try:
        from llm import llm
    except ImportError:
        llm = None


# --- Input Normalization Helpers ---

def _normalize_candidate(cand: Any) -> Dict[str, Any]:
    """Safely normalizes candidate input whether it is a dict, string, or None."""
    if isinstance(cand, dict):
        return dict(cand)
    if isinstance(cand, str):
        # Extract basic skills/name heuristically from text string
        skills = []
        common_skills = [
            "Python", "FastAPI", "Django", "Flask", "SQL", "PostgreSQL", 
            "Docker", "AWS", "React", "JavaScript", "Java", "C++", "Git", "Redis"
        ]
        for skill in common_skills:
            if re.search(rf"\b{re.escape(skill)}\b", cand, re.IGNORECASE):
                skills.append(skill)
        
        return {
            "name": "Candidate",
            "email": "candidate@example.com",
            "skills": skills,
            "resume_text": cand,
            "experience": 3
        }
    return {"name": "Candidate", "skills": [], "resume_text": "", "experience": 0}


def _normalize_job(job: Any) -> Dict[str, Any]:
    """Safely normalizes job input whether it is a dict, string, or None."""
    if isinstance(job, dict):
        return dict(job)
    if isinstance(job, str):
        skills = []
        common_skills = [
            "Python", "FastAPI", "Django", "Flask", "SQL", "PostgreSQL", 
            "Docker", "AWS", "React", "JavaScript", "Java", "C++", "Git", "Redis"
        ]
        for skill in common_skills:
            if re.search(rf"\b{re.escape(skill)}\b", job, re.IGNORECASE):
                skills.append(skill)
        return {
            "job_title": "Software Engineer",
            "required_skills": skills,
            "description": job,
            "location": "Pune",
            "experience": 3
        }
    return {"job_title": "Software Engineer", "required_skills": [], "location": "Remote", "experience": 0}


def _clean_text(val: Any) -> str:
    """Converts any value (int, dict, list, None) safely to a stripped string."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, (int, float, bool)):
        return str(val).strip()
    if isinstance(val, (list, tuple)):
        return " ".join(_clean_text(item) for item in val).strip()
    if isinstance(val, dict):
        return " ".join(f"{k}: {_clean_text(v)}" for k, v in val.items()).strip()
    return str(val).strip()


# --- Screening Question Generation ---

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

def generate_questions(candidate: Any = None, job: Any = None) -> Dict[str, Any]:
    """
    Generates a structured screening questionnaire tailored to the candidate and job.
    Accepts dicts or strings for candidate and job inputs.
    """
    cand_dict = _normalize_candidate(candidate)
    job_dict = _normalize_job(job)

    if llm is not None:
        try:
            prompt = SCREENING_QUESTIONNAIRE_PROMPT.format(
                candidate=json.dumps(cand_dict, indent=2),
                job=json.dumps(job_dict, indent=2)
            )
            response = llm.invoke(prompt)
            content = str(response.content).strip()
            content = re.sub(r"^```(?:json)?", "", content)
            content = re.sub(r"```$", "", content).strip()
            result = json.loads(content)
            
            tech_q = list(result.get("technical_questions", []))
            exp_q = list(result.get("experience_questions", []))
            avail_q = list(result.get("availability_questions", []))
            sal_q = list(result.get("salary_questions", []))
            loc_q = list(result.get("location_questions", []))
            
            all_q = tech_q + exp_q + avail_q + sal_q + loc_q
            return {
                "technical_questions": tech_q,
                "experience_questions": exp_q,
                "availability_questions": avail_q,
                "salary_questions": sal_q,
                "location_questions": loc_q,
                "all_questions": all_q
            }
        except Exception as e:
            logger.warning(f"LLM question generator failed: {str(e)}. Using fallback.")

    return _generate_questions_fallback(cand_dict, job_dict)


def _generate_questions_fallback(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based question generation."""
    cand_skills = candidate.get("skills", [])
    if isinstance(cand_skills, str):
        cand_skills = [s.strip() for s in cand_skills.split(",") if s.strip()]
    job_skills = job.get("required_skills", [])
    if isinstance(job_skills, str):
        job_skills = [s.strip() for s in job_skills.split(",") if s.strip()]
    
    cand_skills_lower = [s.lower() for s in cand_skills]
    matched = [s for s in job_skills if s.lower() in cand_skills_lower]
    missing = [s for s in job_skills if s.lower() not in cand_skills_lower]

    tech_qs = []
    if matched:
        tech_qs.append(f"Can you describe a challenging project where you implemented {matched[0]}?")
    if missing:
        tech_qs.append(f"Have you had hands-on exposure to {missing[0]} or comparable technologies?")
    if not tech_qs:
        tech_qs.append("Describe your core technical stack and architectural design experience.")

    exp_qs = [
        "How many years of relevant production experience do you possess?",
        "What was your key technical contribution in your most recent role?"
    ]

    avail_qs = [
        "What is your official notice period?",
        "When is your earliest possible joining date?"
    ]

    sal_qs = [
        "What is your expected fixed and variable CTC?",
        "Is your salary expectation negotiable depending on the total benefits package?"
    ]

    loc = job.get("location", "the designated office")
    loc_qs = [
        f"Are you comfortable working from {loc} (or hybrid as required)?",
        f"Are you willing to relocate to {loc} if necessary?"
    ]

    all_qs = tech_qs + exp_qs + avail_qs + sal_qs + loc_qs

    return {
        "technical_questions": tech_qs,
        "experience_questions": exp_qs,
        "availability_questions": avail_qs,
        "salary_questions": sal_qs,
        "location_questions": loc_qs,
        "all_questions": all_qs
    }

# Alias for backward compatibility
generate_screening_questionnaire = generate_questions


# --- Answer Evaluation ---

SCREENING_EVALUATION_PROMPT = """
You are an expert recruitment interviewer evaluating a candidate's response to an initial screening question.
Assess the response based on correctness, depth, relevance, and alignment with the job requirements.

Provide:
- score: integer from 0 to 10 (10 = outstanding, 0 = completely wrong, empty, or irrelevant)
- relevance: "High", "Medium", or "Low"
- concerns: list of specific concerns or warning signs
- explanation: brief justification of the score

Return ONLY valid JSON.
{{
    "score": 8,
    "relevance": "High",
    "concerns": [],
    "explanation": "Candidate provided detailed answer with concrete technical examples."
}}

Candidate Profile:
{candidate}

Question:
{question}

Answer:
{answer}
"""

def evaluate_answer(candidate: Any, question: Any, answer: Any) -> Dict[str, Any]:
    """
    Evaluates a single screening answer.
    Safe against any input types (strings, dicts, malformed data, empty strings).
    """
    cand_dict = _normalize_candidate(candidate)
    q_str = _clean_text(question)
    a_str = _clean_text(answer)

    # Fast check for empty or malformed answer
    if not a_str or len(a_str) < 3:
        return {
            "score": 0,
            "relevance": "Low",
            "concerns": ["Empty or non-informative answer provided."],
            "explanation": "No meaningful answer was provided to this screening question."
        }

    if llm is not None:
        try:
            prompt = SCREENING_EVALUATION_PROMPT.format(
                candidate=json.dumps(cand_dict, indent=2),
                question=q_str,
                answer=a_str
            )
            response = llm.invoke(prompt)
            content = str(response.content).strip()
            content = re.sub(r"^```(?:json)?", "", content)
            content = re.sub(r"```$", "", content).strip()
            result = json.loads(content)

            score_val = max(0, min(10, int(result.get("score", 5))))
            return {
                "score": score_val,
                "relevance": str(result.get("relevance", "Medium")),
                "concerns": list(result.get("concerns", [])),
                "explanation": str(result.get("explanation", "Evaluated by AI model."))
            }
        except Exception as e:
            logger.warning(f"LLM answer evaluation failed: {str(e)}. Using rule-based fallback.")

    return _evaluate_answer_fallback(cand_dict, q_str, a_str)


def _evaluate_answer_fallback(candidate: Dict[str, Any], question: str, answer: str) -> Dict[str, Any]:
    """Robust heuristic evaluation for individual answers."""
    q_low = question.lower()
    a_low = answer.lower()
    concerns = []
    
    # 1. Check for negative / non-informative phrases
    weak_phrases = [
        "don't know", "dont know", "no idea", "never heard", "no experience",
        "na", "n/a", "not sure", "none", "nothing", "skip", "pass", "cannot answer"
    ]
    for wp in weak_phrases:
        if wp in a_low and len(a_low) < 80:
            return {
                "score": 1,
                "relevance": "Low",
                "concerns": [f"Candidate indicated lack of knowledge or capability: '{a_low}'"],
                "explanation": "Candidate gave a non-substantive or negative response."
            }

    score = 5

    # 2. Technical question evaluations
    tech_keywords = [
        "python", "fastapi", "django", "flask", "sql", "postgresql", "docker",
        "aws", "react", "redis", "async", "api", "rest", "git", "ci/cd", "microservices"
    ]
    matched_tech = [tk for tk in tech_keywords if tk in a_low]
    
    if any(tk in q_low for tk in tech_keywords):
        if matched_tech:
            score += min(3, len(matched_tech))
        else:
            concerns.append("Response lacks specific technical terminology related to the question.")
            score -= 1

    # 3. Experience indicators
    if "experience" in q_low or "years" in q_low or "project" in q_low:
        if re.search(r'\d+\+?\s*(years?|yrs?|months?)', a_low):
            score += 2
        elif any(w in a_low for w in ["built", "designed", "implemented", "lead", "developed", "architected"]):
            score += 2
        else:
            concerns.append("Did not clearly mention quantified duration or concrete implementation details.")

    # 4. Notice period indicators
    if "notice" in q_low or "join" in q_low:
        if any(w in a_low for w in ["immediate", "15 days", "30 days", "1 month", "2 weeks", "serving notice"]):
            score += 3
        elif any(w in a_low for w in ["90 days", "3 months", "unknown"]):
            score += 1
            concerns.append("Long notice period (90+ days) or uncertain availability.")
        else:
            concerns.append("Notice period was not clearly stated.")

    # 5. Salary / CTC indicators
    if "salary" in q_low or "ctc" in q_low:
        if any(w in a_low for w in ["lpa", "usd", "k", "expected", "open", "negotiable", "per annum"]) or re.search(r'\d+', a_low):
            score += 3
        else:
            concerns.append("Expected CTC or salary expectations were not specified.")

    # 6. Location / Relocation indicators
    if "relocate" in q_low or "location" in q_low or "remote" in q_low or "pune" in q_low:
        if any(w in a_low for w in ["no", "cannot", "unwilling", "not possible", "strictly remote"]):
            score = 2
            concerns.append("Candidate is not willing to relocate or work from the designated office location.")
        elif any(w in a_low for w in ["yes", "comfortable", "open", "relocate", "sure", "happy to"]):
            score += 3
        else:
            concerns.append("Location preference or relocation flexibility remained ambiguous.")

    # Length and depth heuristics
    if len(answer) > 100:
        score += 1
    elif len(answer) < 20 and score > 4:
        score -= 1

    # Clamp boundaries
    score = max(0, min(10, score))
    
    if score >= 8:
        relevance = "High"
    elif score >= 5:
        relevance = "Medium"
    else:
        relevance = "Low"

    explanation = f"Evaluated response with {len(answer)} chars. Relevance: {relevance}."
    if concerns:
        explanation += f" Observations: {'; '.join(concerns)}"

    return {
        "score": score,
        "relevance": relevance,
        "concerns": concerns,
        "explanation": explanation
    }


def evaluate_answers(
    candidate: Any,
    questions: Union[List[Any], Dict[str, Any], str, None],
    answers: Union[List[Any], Dict[str, Any], str, None]
) -> Dict[str, Any]:
    """
    Evaluates a set of answers against a set of questions for a candidate.
    Flexible against multiple question and answer formats:
    - questions as list of strings, list of dicts, or categorized dict
    - answers as list of strings, dict mapping {q: a}, list of dicts, or single string
    Returns overall screening score (0-100), detailed evaluations, strengths, and concerns.
    """
    cand_dict = _normalize_candidate(candidate)

    # 1. Normalize questions into a flat list of question strings
    q_list: List[str] = []
    if isinstance(questions, dict):
        for val in questions.values():
            if isinstance(val, list):
                q_list.extend([_clean_text(item) for item in val if _clean_text(item)])
            elif val:
                q_list.append(_clean_text(val))
    elif isinstance(questions, (list, tuple)):
        for item in questions:
            if isinstance(item, dict):
                q_list.append(_clean_text(item.get("question") or item.get("text") or item))
            else:
                q_list.append(_clean_text(item))
    elif isinstance(questions, str) and questions.strip():
        q_list = [q.strip() for q in questions.split("\n") if q.strip()]

    # Fallback default questions if none provided
    if not q_list:
        q_list = [
            "Explain your primary technical experience.",
            "What is your current notice period and earliest start date?",
            "What are your salary expectations?"
        ]

    # 2. Normalize answers into question-answer pairs
    evaluations = []
    total_score = 0
    all_concerns = []
    all_strengths = []

    if isinstance(answers, dict):
        # Dict mapping {question: answer} or {"q1": "a1"}
        for q in q_list:
            ans = answers.get(q, "")
            if not ans:
                # Try finding key that matches partially
                for k, v in answers.items():
                    if k.lower() in q.lower() or q.lower() in k.lower():
                        ans = v
                        break
            eval_res = evaluate_answer(cand_dict, q, ans)
            eval_res["question"] = q
            eval_res["answer"] = _clean_text(ans)
            evaluations.append(eval_res)
            total_score += eval_res["score"]
            all_concerns.extend(eval_res.get("concerns", []))
            if eval_res["score"] >= 8:
                all_strengths.append(f"Strong response to: {q}")

    elif isinstance(answers, (list, tuple)):
        for i, q in enumerate(q_list):
            ans = answers[i] if i < len(answers) else ""
            if isinstance(ans, dict):
                ans_text = ans.get("answer") or ans.get("response") or str(ans)
            else:
                ans_text = ans
            eval_res = evaluate_answer(cand_dict, q, ans_text)
            eval_res["question"] = q
            eval_res["answer"] = _clean_text(ans_text)
            evaluations.append(eval_res)
            total_score += eval_res["score"]
            all_concerns.extend(eval_res.get("concerns", []))
            if eval_res["score"] >= 8:
                all_strengths.append(f"Strong response to: {q}")

    elif isinstance(answers, str):
        # Single string answer provided for the whole questionnaire or single question
        ans_clean = _clean_text(answers)
        for q in q_list:
            eval_res = evaluate_answer(cand_dict, q, ans_clean)
            eval_res["question"] = q
            eval_res["answer"] = ans_clean
            evaluations.append(eval_res)
            total_score += eval_res["score"]
            all_concerns.extend(eval_res.get("concerns", []))
            if eval_res["score"] >= 8:
                all_strengths.append(f"Strong response to: {q}")
    else:
        # Malformed / None answers
        for q in q_list:
            eval_res = evaluate_answer(cand_dict, q, "")
            eval_res["question"] = q
            eval_res["answer"] = ""
            evaluations.append(eval_res)
            total_score += eval_res["score"]
            all_concerns.extend(eval_res.get("concerns", []))

    num_qs = max(1, len(evaluations))
    avg_score_10 = round(total_score / num_qs, 2)
    screening_score_100 = round(avg_score_10 * 10, 2)

    # Determine overall qualitative outcome
    if screening_score_100 >= 80:
        summary = f"Excellent screening performance ({screening_score_100}%). Candidate displayed strong technical and logistical alignment."
    elif screening_score_100 >= 60:
        summary = f"Satisfactory screening performance ({screening_score_100}%). Candidate meets core criteria with minor follow-up areas."
    else:
        summary = f"Below-threshold screening performance ({screening_score_100}%). Significant concerns identified in screening answers."

    return {
        "screening_score": screening_score_100,
        "average_score_out_of_10": avg_score_10,
        "evaluations": evaluations,
        "concerns": list(set(all_concerns)),
        "strengths": list(set(all_strengths)),
        "summary": summary
    }


# --- Composite Final Scoring Model ---

def calculate_final_score(screening_score: float, ats_score: float, match_score: float) -> float:
    """
    Computes candidate Composite Final Score:
    Final Score = 30% ATS + 50% Match + 20% Screening
    Formula: Final Score = (0.30 * ATS) + (0.50 * Match) + (0.20 * Screening)
    Returns: Float rounded to 2 decimal places.
    """
    # Normalize inputs if on 0-10 scale
    if screening_score <= 10.0 and screening_score > 0:
        screening_score = screening_score * 10.0
    if ats_score <= 10.0 and ats_score > 0:
        ats_score = ats_score * 10.0
    if match_score <= 10.0 and match_score > 0:
        match_score = match_score * 10.0

    final_score = (0.30 * float(ats_score)) + (0.50 * float(match_score)) + (0.20 * float(screening_score))
    return round(max(0.0, min(100.0, final_score)), 2)
