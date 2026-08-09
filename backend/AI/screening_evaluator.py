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

SCREENING_EVALUATION_PROMPT = """
You are an expert interviewer evaluating a candidate's response to an initial screening question.
Assess the response based on correctness, relevance, completeness, and alignment with the job requirements and candidate profile.

Provide a score on a scale of 0 to 10 (where 10 is perfect and 0 is completely irrelevant/wrong).
Determine relevance as "High", "Medium", or "Low".
Identify any concerns or warning signs.
Explain your reasoning.

Return ONLY valid JSON. Do not include markdown styling, "```json" wrappers, or text outside the JSON.

Expected output format:
{{
    "score": 8,
    "relevance": "High",
    "concerns": [],
    "explanation": "Candidate demonstrated practical FastAPI experience."
}}

Candidate Profile:
{candidate}

Question:
{question}

Candidate Answer:
{answer}
"""

def clean_json_response(content: str) -> str:
    content = content.strip()
    content = re.sub(r"^```(?:json)?", "", content)
    content = re.sub(r"```$", "", content)
    return content.strip()

def evaluate_answer(candidate: Dict[str, Any], question: str, answer: str) -> Dict[str, Any]:
    """
    Evaluates a candidate's answer to a screening question.
    Integrates ChatGroq LLM evaluation, falling back to pure-Python heuristics if needed.
    """
    if llm is not None:
        try:
            cand_str = json.dumps(candidate, indent=2)
            prompt = SCREENING_EVALUATION_PROMPT.format(candidate=cand_str, question=question, answer=answer)
            
            logger.info("Invoking LLM for screening answer evaluation...")
            response = llm.invoke(prompt)
            content = clean_json_response(str(response.content))
            
            result = json.loads(content)
            # Ensure correct format
            return {
                "score": int(result.get("score", 0)),
                "relevance": str(result.get("relevance", "Medium")),
                "concerns": list(result.get("concerns", [])),
                "explanation": str(result.get("explanation", "Response evaluated by AI."))
            }
        except Exception as e:
            logger.error(f"LLM screening answer evaluation failed: {str(e)}. Using fallback.")

    # --- Pure-Python Fallback ---
    return evaluate_answer_fallback(candidate, question, answer)

def evaluate_answer_fallback(candidate: Dict[str, Any], question: str, answer: str) -> Dict[str, Any]:
    score = 5
    relevance = "Medium"
    concerns = []
    
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Heuristics based on keyword matching
    # Check for empty answer
    if not answer.strip() or len(answer.strip()) < 5:
        return {
            "score": 0,
            "relevance": "Low",
            "concerns": ["Empty or extremely short answer provided"],
            "explanation": "No meaningful answer was provided to the question."
        }
        
    # Standard technical or experience question evaluations
    if "python" in question_lower:
        if "python" in answer_lower:
            score += 2
            # Check experience extraction if candidate mentions years
            yrs_match = re.search(r'(\d+)\+?\s*(years|year|yrs)', answer_lower)
            if yrs_match:
                score += 1
        else:
            concerns.append("Did not explicitly mention Python in python-specific question response")

    if "fastapi" in question_lower:
        if "fastapi" in answer_lower or "api" in answer_lower:
            score += 2
        else:
            concerns.append("Did not explicitly mention FastAPI or APIs in FastAPI-specific response")
            
    if "notice" in question_lower:
        if any(kw in answer_lower for kw in ["day", "month", "immediate", "week"]):
            score += 3
        else:
            concerns.append("Answer does not explicitly state notice period duration")

    if "ctc" in question_lower or "salary" in question_lower or "expected" in question_lower:
        if any(kw in answer_lower for kw in ["lpa", "usd", "ctc", "salary", "k", "expected", "open", "negotiable"]) or re.search(r'\d+', answer_lower):
            score += 3
        else:
            concerns.append("Answer does not clearly specify expected CTC or salary ranges")

    if "relocate" in question_lower or "pune" in question_lower or "location" in question_lower:
        if any(kw in answer_lower for kw in ["no", "cannot", "not comfortable", "unable"]):
            score = 3
            relevance = "Low"
            concerns.append("Candidate unwilling to relocate or work from the designated office")
        elif any(kw in answer_lower for kw in ["yes", "comfortable", "relocate", "sure", "definitely", "open", "pune"]):
            score += 3
        else:
            concerns.append("Vague location/relocation preference response")


    # Limit score boundaries
    score = max(0, min(10, score))
    if score >= 8:
        relevance = "High"
    elif score >= 5:
        relevance = "Medium"
    else:
        relevance = "Low"
        
    explanation = f"Evaluated using fallback rules. Length of response: {len(answer)} characters."
    if concerns:
        explanation += f" Detected concerns regarding: {', '.join(concerns)}"

    return {
        "score": score,
        "relevance": relevance,
        "concerns": concerns,
        "explanation": explanation
    }

def calculate_final_score(screening_score: float, ats_score: float, match_score: float) -> float:
    """
    Calculates the final candidate composite score:
    Weighted logic: 30% ATS + 50% Match + 20% Screening.
    Ensures final score is returned rounded to 2 decimal places.
    """
    return round((0.3 * ats_score) + (0.5 * match_score) + (0.2 * screening_score), 2)
