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

FEEDBACK_ANALYSIS_PROMPT = """
You are an AI Recruitment Analyst.
Analyze the provided list of interviewer/recruiter feedback comments and ratings for a candidate.
Synthesize the comments to extract:
- average_rating (float, calculated from ratings if provided on a 1-5 scale, or inferred from comments on a 1.0 - 5.0 scale)
- positive_points (list of key strengths and highlights mentioned)
- concerns (list of limitations, weaknesses, or concerns highlighted)
- overall_feedback (brief summary of overall suitability)

Return ONLY valid JSON. Do not include markdown styling, "```json" wrappers, or text outside the JSON.

Expected output format:
{{
    "average_rating": 4.2,
    "positive_points": [
        "Strong Python knowledge",
        "Good communication"
    ],
    "concerns": [
        "Limited AWS experience"
    ],
    "overall_feedback": "Strong technical candidate"
}}

Feedback Data:
{feedbacks}
"""

def clean_json_response(content: str) -> str:
    content = content.strip()
    content = re.sub(r"^```(?:json)?", "", content)
    content = re.sub(r"```$", "", content)
    return content.strip()

def analyze_feedback(feedbacks: List[Any]) -> Dict[str, Any]:
    """
    Analyzes recruiter/interviewer feedback remarks.
    Integrates ChatGroq LLM, falling back to Python heuristics if needed.
    """
    if not feedbacks:
        return {
            "average_rating": 0.0,
            "positive_points": [],
            "concerns": ["No feedback submitted yet"],
            "overall_feedback": "No feedback comments available to analyze."
        }

    if llm is not None:
        try:
            feedbacks_str = json.dumps(feedbacks, indent=2)
            prompt = FEEDBACK_ANALYSIS_PROMPT.format(feedbacks=feedbacks_str)
            
            logger.info("Invoking LLM for feedback analysis...")
            response = llm.invoke(prompt)
            content = clean_json_response(str(response.content))
            
            result = json.loads(content)
            # Ensure correct format
            return {
                "average_rating": float(result.get("average_rating", 3.0)),
                "positive_points": list(result.get("positive_points", [])),
                "concerns": list(result.get("concerns", [])),
                "overall_feedback": str(result.get("overall_feedback", "Feedback analyzed by AI."))
            }
        except Exception as e:
            logger.error(f"LLM feedback analysis failed: {str(e)}. Using fallback.")

    # --- Pure-Python Fallback ---
    return analyze_feedback_fallback(feedbacks)

def analyze_feedback_fallback(feedbacks: List[Any]) -> Dict[str, Any]:
    total_rating = 0.0
    rating_count = 0
    positive_points = []
    concerns = []
    
    # Positive/negative word lists for basic keyword analysis
    pos_keywords = ["good", "strong", "excellent", "great", "well", "best", "solid", "nice", "awesome", "fantastic", "proficient", "clear", "communicative"]
    neg_keywords = ["limit", "lack", "weak", "concern", "improvement", "poor", "difficult", "struggle", "hesitant", "no", "miss"]
    
    for item in feedbacks:
        comment = ""
        rating = None
        
        # Determine text and rating
        if isinstance(item, dict):
            comment = str(item.get("comment") or item.get("notes") or item.get("feedback") or "")
            rating = item.get("rating") or item.get("score")
        elif isinstance(item, str):
            comment = item
            # Look for score pattern in string e.g. "4/5" or "rating: 5"
            match = re.search(r'(\d+)\s*(?:/|\bout of\b)\s*5', comment.lower())
            if match:
                rating = float(match.group(1))
            else:
                match_digit = re.search(r'\b([1-5])\b', comment)
                if match_digit:
                    rating = float(match_digit.group(1))
        
        if rating is not None:
            try:
                val = float(rating)
                # Normalize to 1-5 scale if it was out of 10
                if val > 5.0 and val <= 10.0:
                    val = val / 2.0
                total_rating += val
                rating_count += 1
            except ValueError:
                pass
                
        # Extract keywords
        comment_lower = comment.lower()
        sentences = [s.strip() for s in re.split(r'[\.\n,;]', comment) if s.strip()]
        for s in sentences:
            s_lower = s.lower()
            if any(w in s_lower for w in pos_keywords):
                # Clean clean string
                clean_s = re.sub(r'^(but|and|so|overall|candidate|has)\s+', '', s, flags=re.IGNORECASE).strip()
                if len(clean_s) > 10 and clean_s not in positive_points:
                    positive_points.append(clean_s)
            if any(w in s_lower for w in neg_keywords):
                clean_s = re.sub(r'^(but|and|so|overall|candidate|has)\s+', '', s, flags=re.IGNORECASE).strip()
                if len(clean_s) > 10 and clean_s not in concerns:
                    concerns.append(clean_s)

    # Compute average rating
    if rating_count > 0:
        avg_rating = round(total_rating / rating_count, 1)
    else:
        # Infer rating from positive/negative words count
        pos_cnt = len(positive_points)
        neg_cnt = len(concerns)
        if pos_cnt + neg_cnt > 0:
            avg_rating = round(3.0 + (pos_cnt - neg_cnt) * 0.5, 1)
            avg_rating = max(1.0, min(5.0, avg_rating))
        else:
            avg_rating = 3.0

    # Ensure some fallback values
    if not positive_points:
        positive_points = ["Technical skillset appears compatible"]
    if not concerns:
        concerns = ["No major concerns detected from comments"]
        
    overall_feedback = f"Feedback analysis completed from {len(feedbacks)} review entries. Summary rating of {avg_rating}/5."

    return {
        "average_rating": avg_rating,
        "positive_points": positive_points[:5],
        "concerns": concerns[:5],
        "overall_feedback": overall_feedback
    }
