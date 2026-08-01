import os
import sys
import logging
from typing import TypedDict, List, Dict, Any, Optional, cast
from sqlalchemy.orm import Session

# Add project root and backend to PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models import Candidate, Job, CandidateScore, Recommendation, Resume
from AI.document_reader import extract_resume_text
from AI.resume_extractor import extract_candidate_info
from AI.job_extractor import extract_job_info

logger = logging.getLogger(__name__)

# --- Typed Workflow State ---
class AgentState(TypedDict):
    file_path: Optional[str]
    resume_text: Optional[str]
    job_text: Optional[str]
    candidate_data: Optional[Dict[str, Any]]
    job_data: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    score_details: Optional[Dict[str, Any]]
    recommendation_details: Optional[Dict[str, Any]]
    ranking_details: Optional[List[Dict[str, Any]]]
    errors: List[str]
    retry_count: int
    candidate_id: Optional[int]
    job_id: Optional[int]
    db: Optional[Any]

# --- Workflow Helper Functions ---

def get_db_session(state: AgentState):
    """Returns database session from state or a new connection."""
    if "db" in state and state["db"] is not None:
        return state["db"], False
    return SessionLocal(), True


# --- Workflow Nodes ---

def document_reader_node(state: AgentState) -> Dict[str, Any]:
    """Reads raw text from the resume file."""
    logger.info("LangGraph Node: Document Reader started.")
    file_path = state.get("file_path")
    if not file_path:
        return {"errors": state.get("errors", []) + ["No file path provided."]}
    
    try:
        text = extract_resume_text(file_path)
        return {"resume_text": text}
    except Exception as e:
        logger.error(f"Error in document reader node: {str(e)}")
        return {"errors": state.get("errors", []) + [f"Read failed: {str(e)}"]}

def resume_extraction_node(state: AgentState) -> Dict[str, Any]:
    """Extracts candidate profile data using the LLM parser."""
    logger.info("LangGraph Node: Resume Extraction started.")
    text = state.get("resume_text")
    if not text:
        return {"errors": state.get("errors", []) + ["No resume text available for parsing."]}

    try:
        cand_info = cast(Dict[str, Any], extract_candidate_info(text))
    except Exception as e:
        logger.warning(f"LLM resume extraction failed, trying regex fallback: {str(e)}")
        try:
            from app.services.extractor import extract_candidate_info as regex_extract
            cand_info = cast(Dict[str, Any], regex_extract(text))
        except Exception as e2:
            logger.error(f"Fallback extraction failed: {str(e2)}")
            return {"errors": state.get("errors", []) + [f"Resume extraction failed: {str(e2)}"]}

    # Ensure we support new fields in parsed output
    if "certifications" not in cand_info:
        cand_info["certifications"] = []
    if "achievements" not in cand_info:
        cand_info["achievements"] = []
    if "languages" not in cand_info:
        cand_info["languages"] = ["English"]
    if "soft_skills" not in cand_info:
        cand_info["soft_skills"] = []
    if "current_company" not in cand_info:
        cand_info["current_company"] = ""
    if "employment_gap" not in cand_info:
        cand_info["employment_gap"] = False

    return {"candidate_data": cand_info}

def job_extraction_node(state: AgentState) -> Dict[str, Any]:
    """Extracts job requirements and metadata."""
    logger.info("LangGraph Node: Job Extraction started.")
    job_text = state.get("job_text")
    if not job_text:
        # Try to resolve from DB using job_id
        job_id = state.get("job_id")
        if job_id:
            db, should_close = get_db_session(state)
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    reqs = cast(List[str], job.requirements) if job.requirements is not None else []
                    job_text = f"Title: {job.title}\nDescription: {job.description}\nRequirements: {', '.join(reqs)}\nExperience: {job.experience_required} years"
            finally:
                if should_close:
                    db.close()
                
    if not job_text:
        return {"errors": state.get("errors", []) + ["No job requirements text available."]}

    try:
        job_info = extract_job_info(job_text)
    except Exception as e:
        logger.warning(f"LLM job extraction failed, trying regex fallback: {str(e)}")
        # Internal regex job extractor fallback
        import re
        skill_database = ["Python", "Java", "C++", "SQL", "AWS", "FastAPI", "React", "JavaScript", "Docker", "Git", "PostgreSQL", "Redis"]
        skills = []
        for skill in skill_database:
            pattern = rf'\b{re.escape(skill.lower())}\b'
            if skill == "C++":
                pattern = r'c\+\+'
            if re.search(pattern, job_text.lower()):
                skills.append(skill)
                
        exp = 0
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience', job_text, re.IGNORECASE)
        if exp_match:
            exp = int(exp_match.group(1))
            
        title = "Backend Developer"
        for line in job_text.split("\n"):
            if "title" in line.lower() or "role" in line.lower():
                title_match = re.search(r'(?:title|role)\s*:\s*([^\n]+)', line, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                    break
        job_info = {
            "job_title": title,
            "required_skills": skills,
            "experience": exp,
            "salary_range": "",
            "notice_period": ""
        }

    return {"job_data": job_info}

def validation_node(state: AgentState) -> Dict[str, Any]:
    """Validates the parsed data and controls loop retries."""
    logger.info("LangGraph Node: Validation started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    errors = list(state.get("errors", []))
    retry_count = state.get("retry_count", 0)
    is_valid = True
    
    if not cand or not cand.get("name") or cand.get("name") == "Not Available":
        is_valid = False
        errors.append("Validation failed: Candidate name is missing.")
    if not cand or not cand.get("email") or cand.get("email") == "Not Available":
        is_valid = False
        errors.append("Validation failed: Candidate email is missing.")
    if not cand or not cand.get("skills"):
        is_valid = False
        errors.append("Validation failed: Skills list is empty.")

    if not is_valid:
        retry_count += 1
        logger.warning(f"Validation failed (Attempt {retry_count}). Errors: {errors[-1]}")

    return {
        "validation_results": {"is_valid": is_valid, "retry_count": retry_count},
        "errors": errors,
        "retry_count": retry_count
    }

def candidate_scoring_node(state: AgentState) -> Dict[str, Any]:
    """Scores candidate using the enhanced 11-point criteria algorithm."""
    logger.info("LangGraph Node: Candidate Scoring started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Scoring skipped: Missing candidate or job data."]}

    try:
        # Import enhanced scorer
        from AI.scorer import calculate_enhanced_score
        score_details = calculate_enhanced_score(cand, job)
        return {"score_details": score_details}
    except Exception as e:
        logger.error(f"Error in candidate scoring node: {str(e)}")
        return {"errors": state.get("errors", []) + [f"Scoring failed: {str(e)}"]}

def recommendation_generation_node(state: AgentState) -> Dict[str, Any]:
    """Generates upskilling paths, custom questions, summaries, and explainable justifications."""
    logger.info("LangGraph Node: Recommendation Generation started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    score_details = state.get("score_details", {})
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Skipped recommendation: Missing input data."]}

    db, should_close = get_db_session(state)
    try:
        # Resolve dummy candidate/job IDs if not provided to run service helpers
        cand_db = db.query(Candidate).filter(Candidate.email == cand.get("email")).first()
        job_db = db.query(Job).filter(Job.title == job.get("job_title")).first()
        
        cand_id = int(cast(Any, state.get("candidate_id") or (cand_db.id if cand_db else 1)))
        job_id = int(cast(Any, state.get("job_id") or (job_db.id if job_db else 1)))

        from app.services.ai_pipeline import (
            summarize_candidate, analyze_skill_gap,
            generate_interview_questions, generate_explainable_recommendation
        )

        # 1. AI Summary (includes key strengths, technical skills, areas for improvement, overall suitability)
        summary_res = summarize_candidate(cand_id, db)
        
        # 2. Skill Gap Analysis (missing skills, recommended courses, learning paths, upskilling recommendations)
        gap_res = analyze_skill_gap(cand_id, job_id, db)
        
        # 3. AI Interview Questions (Technical, HR, Coding, Behavioral)
        questions_res = generate_interview_questions(cand_id, job_id, db)
        
        # 4. Explainable fit recommendations
        rec_res = generate_explainable_recommendation(cand_id, job_id, db)

        recommendation_details = {
            "ai_summary": summary_res.get("ai_summary"),
            "skill_gap_report": gap_res,
            "interview_questions": [
                {"id": q.id, "question": q.question, "expected_answer": q.expected_answer, "category": q.category}
                for q in questions_res
            ],
            "recommendation": rec_res
        }
        
        return {"recommendation_details": recommendation_details}
    except Exception as e:
        logger.error(f"Error in recommendation generation node: {str(e)}")
        return {"errors": state.get("errors", []) + [f"Recommendation generation failed: {str(e)}"]}
    finally:
        if should_close:
            db.close()

def candidate_ranking_node(state: AgentState) -> Dict[str, Any]:
    """Sorts/ranks candidate list details if multiple profiles are processed."""
    logger.info("LangGraph Node: Candidate Ranking started.")
    score_details = state.get("score_details") or {}
    cand_data = state.get("candidate_data") or {}
    rec_details = state.get("recommendation_details") or {}
    rec_dict = rec_details.get("recommendation") or {}
    rec_val = rec_dict.get("recommendation", "Under Review") if isinstance(rec_dict, dict) else "Under Review"
    
    ranking_entry = {
        "name": cand_data.get("name"),
        "email": cand_data.get("email"),
        "match_percentage": score_details.get("match_percentage", 0.0),
        "recommendation": rec_val
    }
    
    return {"ranking_details": [ranking_entry]}

def store_results_node(state: AgentState) -> Dict[str, Any]:
    """Persists final score, summary, and recommendation attributes directly to DB."""
    logger.info("LangGraph Node: Store Results started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    score_details = state.get("score_details") or {}
    rec_details = state.get("recommendation_details") or {}
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Storage skipped: Missing candidate or job data."]}

    db, should_close = get_db_session(state)
    try:
        # Resolve candidate
        candidate_db = db.query(Candidate).filter(Candidate.email == cand.get("email")).first()
        if candidate_db:
            candidate_db_any = cast(Any, candidate_db)
            # Update score and summary fields in Candidate DB
            candidate_db_any.ai_summary = rec_details.get("ai_summary", "")
            
            # Find score record
            job_db = db.query(Job).filter(Job.title == job.get("job_title")).first()
            if job_db:
                score_rec = db.query(CandidateScore).filter(
                    CandidateScore.candidate_id == candidate_db.id,
                    CandidateScore.job_id == job_db.id
                ).first()
                if score_rec:
                    score_rec_any = cast(Any, score_rec)
                    score_rec_any.match_score = score_details.get("match_percentage", 0.0)
                    score_rec_any.skill_gap_report = rec_details.get("skill_gap_report")
                
                # Update recommendation record
                rec_db = db.query(Recommendation).filter(
                    Recommendation.candidate_id == candidate_db.id,
                    Recommendation.job_id == job_db.id
                ).first()
                if rec_db and "recommendation" in rec_details:
                    rec_info = rec_details["recommendation"]
                    if isinstance(rec_info, dict):
                        rec_db_any = cast(Any, rec_db)
                        rec_db_any.recommendation = str(rec_info.get("recommendation", "Under Review"))
                        rec_db_any.strengths = rec_info.get("strengths", [])
                        rec_db_any.weaknesses = rec_info.get("weaknesses", [])
                        rec_db_any.ai_summary = str(rec_info.get("justification", ""))
            
            db.commit()
            logger.info("Store Results Node: Workflow results successfully stored in DB.")
        
        return {}
    except Exception as e:
        logger.error(f"Error in store results node: {str(e)}")
        db.rollback()
        return {"errors": state.get("errors", []) + [f"Store results failed: {str(e)}"]}
    finally:
        if should_close:
            db.close()


# --- Compile Workflow Graph (LangGraph or Fallback) ---

try:
    from langgraph.graph import StateGraph, START, END  # type: ignore
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("document_reader", document_reader_node)
    workflow.add_node("resume_extraction", resume_extraction_node)
    workflow.add_node("job_extraction", job_extraction_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("candidate_scoring", candidate_scoring_node)
    workflow.add_node("recommendation_generation", recommendation_generation_node)
    workflow.add_node("candidate_ranking", candidate_ranking_node)
    workflow.add_node("store_results", store_results_node)
    
    # Add edges
    workflow.add_edge(START, "document_reader")
    workflow.add_edge("document_reader", "resume_extraction")
    workflow.add_edge("resume_extraction", "job_extraction")
    workflow.add_edge("job_extraction", "validation")
    
    def route_after_validation(state: AgentState):
        val_results = state.get("validation_results") or {}
        if val_results.get("is_valid", True) or state.get("retry_count", 0) >= 3:
            return "candidate_scoring"
        else:
            return "resume_extraction"

    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "candidate_scoring": "candidate_scoring",
            "resume_extraction": "resume_extraction"
        }
    )
    
    workflow.add_edge("candidate_scoring", "recommendation_generation")
    workflow.add_edge("recommendation_generation", "candidate_ranking")
    workflow.add_edge("candidate_ranking", "store_results")
    workflow.add_edge("store_results", END)
    
    app_graph = workflow.compile()
    logger.info("AI Workflow Graph compiled successfully using LangGraph.")

except ImportError:
    logger.warning("LangGraph not installed. Creating fallback workflow executor.")
    
    class CompiledGraphFallback:
        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            state: AgentState = {
                "file_path": inputs.get("file_path"),
                "resume_text": inputs.get("resume_text"),
                "job_text": inputs.get("job_text"),
                "candidate_id": inputs.get("candidate_id"),
                "job_id": inputs.get("job_id"),
                "db": inputs.get("db"),
                "candidate_data": None,
                "job_data": None,
                "validation_results": None,
                "score_details": None,
                "recommendation_details": None,
                "ranking_details": None,
                "errors": [],
                "retry_count": 0
            }
            
            # 1. Read document
            res = document_reader_node(state)
            state.update(cast(AgentState, res))
            
            # Loop for extraction & validation
            while state["retry_count"] < 3:
                # 2. Extract Candidate
                res = resume_extraction_node(state)
                state.update(cast(AgentState, res))
                
                # 3. Extract Job
                res = job_extraction_node(state)
                state.update(cast(AgentState, res))
                
                # 4. Validate
                res = validation_node(state)
                state.update(cast(AgentState, res))
                
                val_results = state.get("validation_results") or {}
                if val_results.get("is_valid", True):
                    break
            
            # 5. Score Candidate
            res = candidate_scoring_node(state)
            state.update(cast(AgentState, res))
            
            # 6. Generate Recommendations
            res = recommendation_generation_node(state)
            state.update(cast(AgentState, res))
            
            # 7. Rank Candidate
            res = candidate_ranking_node(state)
            state.update(cast(AgentState, res))
            
            # 8. Store Results
            res = store_results_node(state)
            state.update(cast(AgentState, res))
            
            return cast(Dict[str, Any], state)

    app_graph = CompiledGraphFallback()
