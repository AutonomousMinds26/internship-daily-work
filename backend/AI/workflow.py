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
from AI.screening import generate_questions, evaluate_answers, calculate_final_score
from AI.predictive import predict_hiring_outcome
from AI.explainability import generate_candidate_explainability

logger = logging.getLogger(__name__)

# --- Typed Workflow State ---
class AgentState(TypedDict):
    file_path: Optional[str]
    resume_text: Optional[str]
    job_text: Optional[str]
    candidate_data: Optional[Dict[str, Any]]
    job_data: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    ats_details: Optional[Dict[str, Any]]
    match_details: Optional[Dict[str, Any]]
    score_details: Optional[Dict[str, Any]]
    screening_details: Optional[Dict[str, Any]]
    recommendation_details: Optional[Dict[str, Any]]
    predictive_details: Optional[Dict[str, Any]]
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
    """1. Document Reader: Reads raw text from the resume file."""
    logger.info("LangGraph Node 1: Document Reader started.")
    file_path = state.get("file_path")
    if not file_path:
        # If resume_text is already provided, pass through
        if state.get("resume_text"):
            return {"resume_text": state.get("resume_text")}
        return {"errors": state.get("errors", []) + ["No file path or resume text provided."]}
    
    try:
        text = extract_resume_text(file_path)
        return {"resume_text": text}
    except Exception as e:
        logger.error(f"Error in document reader node: {str(e)}")
        return {"errors": state.get("errors", []) + [f"Read failed: {str(e)}"]}


def resume_extraction_node(state: AgentState) -> Dict[str, Any]:
    """2. Resume Extraction: Extracts candidate profile data using the LLM/regex parser."""
    logger.info("LangGraph Node 2: Resume Extraction started.")
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

    cand_dict = dict(cand_info) if isinstance(cand_info, dict) else {}
    for k in ["certifications", "achievements", "soft_skills"]:
        if k not in cand_dict:
            cand_dict[k] = []
    if "languages" not in cand_dict:
        cand_dict["languages"] = ["English"]
    if "current_company" not in cand_dict:
        cand_dict["current_company"] = ""
    if "employment_gap" not in cand_dict:
        cand_dict["employment_gap"] = False

    return {"candidate_data": cand_dict}


def job_extraction_node(state: AgentState) -> Dict[str, Any]:
    """3. Job Extraction: Extracts job requirements and metadata."""
    logger.info("LangGraph Node 3: Job Extraction started.")
    job_text = state.get("job_text")
    if not job_text:
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
        job_text = "Job Title: Software Engineer\nRequired Skills: Python, FastAPI, PostgreSQL\nExperience: 3 years"

    try:
        job_info = extract_job_info(job_text)
    except Exception as e:
        logger.warning(f"LLM job extraction failed, trying fallback: {str(e)}")
        import re
        skill_database = ["Python", "Java", "C++", "SQL", "AWS", "FastAPI", "React", "JavaScript", "Docker", "Git", "PostgreSQL", "Redis"]
        skills = [s for s in skill_database if re.search(rf'\b{re.escape(s.lower())}\b', job_text.lower())]
        job_info = {
            "job_title": "Software Engineer",
            "required_skills": skills if skills else ["Python", "FastAPI"],
            "experience": 3,
            "salary_range": "",
            "notice_period": ""
        }

    return {"job_data": job_info}


def validation_node(state: AgentState) -> Dict[str, Any]:
    """4. Validation: Validates parsed data and controls conditional retry loops."""
    logger.info("LangGraph Node 4: Validation started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    errors = list(state.get("errors", []))
    retry_count = state.get("retry_count", 0)
    is_valid = True
    
    if not cand or not cand.get("name") or cand.get("name") == "Not Available":
        is_valid = False
        errors.append("Validation warning: Candidate name is missing.")
    if not cand or not cand.get("skills"):
        is_valid = False
        errors.append("Validation warning: Candidate skills are empty.")

    if not is_valid:
        retry_count += 1

    return {
        "validation_results": {"is_valid": is_valid, "retry_count": retry_count},
        "errors": errors,
        "retry_count": retry_count
    }


def ats_analysis_node(state: AgentState) -> Dict[str, Any]:
    """5. ATS Analysis: Analyzes keyword coverage, formatting, and relevance."""
    logger.info("LangGraph Node 5: ATS Analysis started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["ATS Analysis skipped: Missing data."]}
    
    try:
        from AI.ats_analyzer import analyze_ats
        cand_dict = dict(cand)
        if "resume_text" not in cand_dict:
            cand_dict["resume_text"] = state.get("resume_text", "")
            
        ats_res = analyze_ats(cand_dict, job)
        return {"ats_details": ats_res}
    except Exception as e:
        logger.error(f"Error in ATS analysis node: {str(e)}")
        return {
            "ats_details": {"ats_score": 70.0, "match_verdict": "Moderate", "concerns": []},
            "errors": state.get("errors", []) + [f"ATS Analysis failed: {str(e)}"]
        }


def candidate_matching_node(state: AgentState) -> Dict[str, Any]:
    """6. Candidate Matching: Semantic & LLM skill matching."""
    logger.info("LangGraph Node 6: Candidate Matching started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Candidate Matching skipped."]}

    try:
        from AI.ai_matcher import ai_match_candidate
        match_res = ai_match_candidate(cand, job)
        return {"match_details": match_res}
    except Exception as e:
        logger.error(f"Error in candidate matching node: {str(e)}")
        return {"match_details": {"match_percentage": 65.0, "matched_skills": []}}


def candidate_scoring_node(state: AgentState) -> Dict[str, Any]:
    """7. Candidate Scoring: Enhanced 11-point weighted scoring."""
    logger.info("LangGraph Node 7: Candidate Scoring started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Scoring skipped."]}

    try:
        from AI.scorer import calculate_enhanced_score
        score_details = calculate_enhanced_score(cand, job)
        return {"score_details": score_details}
    except Exception as e:
        logger.error(f"Error in candidate scoring node: {str(e)}")
        return {"errors": state.get("errors", []) + [f"Scoring failed: {str(e)}"]}


def screening_node(state: AgentState) -> Dict[str, Any]:
    """8. Screening: Generates questionnaire and evaluates baseline responses."""
    logger.info("LangGraph Node 8: Screening started.")
    cand = state.get("candidate_data") or {}
    job = state.get("job_data") or {}

    try:
        questions = generate_questions(cand, job)
        # Default mock answers from candidate profile for end-to-end evaluation
        mock_answers = [
            f"I have extensive experience with {', '.join(cand.get('skills', ['Python'])[:2])}.",
            f"I have {cand.get('experience', 3)} years of professional experience.",
            "30 days official notice period.",
            "Expected CTC is negotiable based on standard market bands.",
            "Yes, I am comfortable working from the designated office."
        ]
        eval_res = evaluate_answers(cand, questions.get("all_questions", []), mock_answers)
        return {"screening_details": eval_res}
    except Exception as e:
        logger.error(f"Error in screening node: {str(e)}")
        return {
            "screening_details": {
                "screening_score": 75.0,
                "summary": "Screening completed with fallback baseline."
            }
        }


def recommendation_generation_node(state: AgentState) -> Dict[str, Any]:
    """9. Recommendation Generation: Summaries, upskilling gap analysis, and questions."""
    logger.info("LangGraph Node 9: Recommendation Generation started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    
    if not cand or not job:
        return {"errors": state.get("errors", []) + ["Skipped recommendation: Missing input data."]}

    db, should_close = get_db_session(state)
    try:
        cand_db = db.query(Candidate).filter(Candidate.email == cand.get("email")).first()
        job_db = db.query(Job).filter(Job.title == job.get("job_title")).first()
        
        cand_id = int(cast(Any, state.get("candidate_id") or (cand_db.id if cand_db else 1)))
        job_id = int(cast(Any, state.get("job_id") or (job_db.id if job_db else 1)))

        from app.services.ai_pipeline import (
            summarize_candidate, analyze_skill_gap,
            generate_interview_questions, generate_explainable_recommendation
        )

        try:
            summary_res = summarize_candidate(cand_id, db)
        except Exception:
            summary_res = {"ai_summary": "Qualified candidate matching requirements."}
            
        try:
            gap_res = analyze_skill_gap(cand_id, job_id, db)
        except Exception:
            gap_res = {"missing_skills": [], "learning_path": []}
            
        try:
            questions_res = generate_interview_questions(cand_id, job_id, db)
            interview_qs = [
                {"id": q.id, "question": q.question, "expected_answer": q.expected_answer, "category": q.category}
                for q in questions_res
            ]
        except Exception:
            interview_qs = []
            
        try:
            rec_res = generate_explainable_recommendation(cand_id, job_id, db)
        except Exception:
            rec_res = {"recommendation": "Advance", "strengths": [], "weaknesses": []}

        recommendation_details = {
            "ai_summary": summary_res.get("ai_summary"),
            "skill_gap_report": gap_res,
            "interview_questions": interview_qs,
            "recommendation": rec_res
        }
        return {"recommendation_details": recommendation_details}
    except Exception as e:
        logger.error(f"Error in recommendation generation node: {str(e)}")
        return {"recommendation_details": {"recommendation": {"recommendation": "Review"}}}
    finally:
        if should_close:
            db.close()


def predictive_analytics_node(state: AgentState) -> Dict[str, Any]:
    """10. Predictive Analytics & AI Explainability: Computes Composite Final Score, Probability, Risk."""
    logger.info("LangGraph Node 10: Predictive Analytics started.")
    cand = state.get("candidate_data") or {}
    job = state.get("job_data") or {}
    ats_res = state.get("ats_details") or {}
    score_res = state.get("score_details") or {}
    scr_res = state.get("screening_details") or {}

    ats_score = float(ats_res.get("ats_score", 70.0))
    match_score = float(score_res.get("match_percentage", 70.0))
    screening_score = float(scr_res.get("screening_score", 75.0))

    final_score = calculate_final_score(
        screening_score=screening_score,
        ats_score=ats_score,
        match_score=match_score
    )

    explainability = generate_candidate_explainability(
        candidate=cand,
        job=job,
        ats_score=ats_score,
        match_score=match_score,
        screening_score=screening_score,
        ats_details=ats_res,
        score_details=score_res
    )

    return {"predictive_details": explainability}


def candidate_ranking_node(state: AgentState) -> Dict[str, Any]:
    """11a. Candidate Ranking."""
    logger.info("LangGraph Node 11a: Candidate Ranking started.")
    cand_data = state.get("candidate_data") or {}
    pred_details = state.get("predictive_details") or {}
    
    ranking_entry = {
        "name": cand_data.get("name"),
        "email": cand_data.get("email"),
        "final_score": pred_details.get("final_score", 0.0),
        "hiring_probability": pred_details.get("hiring_probability_percentage", "70%"),
        "risk_level": pred_details.get("risk_level", "Medium"),
        "recommendation": pred_details.get("recommendation", "Consider")
    }
    return {"ranking_details": [ranking_entry]}


def store_results_node(state: AgentState) -> Dict[str, Any]:
    """11b. Store Results: Persists final composite score, probability, and recommendations to DB."""
    logger.info("LangGraph Node 11b: Store Results started.")
    cand = state.get("candidate_data")
    job = state.get("job_data")
    pred = state.get("predictive_details") or {}
    rec_details = state.get("recommendation_details") or {}
    
    if not cand or not job:
        return {}

    db, should_close = get_db_session(state)
    try:
        candidate_db = db.query(Candidate).filter(Candidate.email == cand.get("email")).first()
        if candidate_db:
            candidate_db_any = cast(Any, candidate_db)
            candidate_db_any.ats_score = pred.get("ats_score", 0.0)
            candidate_db_any.match_score = pred.get("match_score", 0.0)
            candidate_db_any.screening_score = pred.get("screening_score", 0.0)
            candidate_db_any.final_score = pred.get("final_score", 0.0)
            candidate_db_any.ai_summary = pred.get("explanation", "")
            
            db.commit()
            logger.info("Store Results Node: Successfully saved pipeline scores in DB.")
        return {}
    except Exception as e:
        logger.error(f"Error saving workflow results in DB: {str(e)}")
        db.rollback()
        return {}
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
    workflow.add_node("ats_analysis", ats_analysis_node)
    workflow.add_node("candidate_matching", candidate_matching_node)
    workflow.add_node("candidate_scoring", candidate_scoring_node)
    workflow.add_node("screening", screening_node)
    workflow.add_node("recommendation_generation", recommendation_generation_node)
    workflow.add_node("predictive_analytics", predictive_analytics_node)
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
            return "ats_analysis"
        else:
            return "resume_extraction"

    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "ats_analysis": "ats_analysis",
            "resume_extraction": "resume_extraction"
        }
    )
    
    workflow.add_edge("ats_analysis", "candidate_matching")
    workflow.add_edge("candidate_matching", "candidate_scoring")
    workflow.add_edge("candidate_scoring", "screening")
    workflow.add_edge("screening", "recommendation_generation")
    workflow.add_edge("recommendation_generation", "predictive_analytics")
    workflow.add_edge("predictive_analytics", "candidate_ranking")
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
                "ats_details": None,
                "match_details": None,
                "score_details": None,
                "screening_details": None,
                "recommendation_details": None,
                "predictive_details": None,
                "ranking_details": None,
                "errors": [],
                "retry_count": 0
            }
            
            res = document_reader_node(state)
            state.update(cast(AgentState, res))
            
            while state["retry_count"] < 3:
                res = resume_extraction_node(state)
                state.update(cast(AgentState, res))
                
                res = job_extraction_node(state)
                state.update(cast(AgentState, res))
                
                res = validation_node(state)
                state.update(cast(AgentState, res))
                
                val_results = state.get("validation_results") or {}
                if val_results.get("is_valid", True):
                    break
            
            for node_func in [
                ats_analysis_node,
                candidate_matching_node,
                candidate_scoring_node,
                screening_node,
                recommendation_generation_node,
                predictive_analytics_node,
                candidate_ranking_node,
                store_results_node
            ]:
                res = node_func(state)
                state.update(cast(AgentState, res))
            
            return cast(Dict[str, Any], state)

    app_graph = CompiledGraphFallback()


def run_recruitment_pipeline(
    file_path: Optional[str] = None,
    resume_text: Optional[str] = None,
    job_text: Optional[str] = None,
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Independent executor for the full recruitment AI pipeline.
    Runs Resume -> Document Reader -> Resume Extraction -> Job Extraction -> Validation 
         -> ATS Analysis -> Candidate Matching -> Candidate Scoring -> Screening 
         -> Recommendation -> Predictive Analytics.
    """
    inputs = {
        "file_path": file_path,
        "resume_text": resume_text,
        "job_text": job_text,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "db": db
    }
    return app_graph.invoke(inputs)


def run_lifecycle_recruitment_graph(
    candidate_id: int,
    job_id: int,
    candidate_data: Dict[str, Any],
    job_data: Dict[str, Any],
    assessment_provider: str = "HackerRank"
) -> Dict[str, Any]:
    """
    Executes the multi-stage LangGraph recruitment lifecycle workflow:
    Matching -> Screening -> Assessment -> Interview Coordination -> Feedback -> Verification -> Offer.
    """
    from AI.recruitment_graph import recruitment_graph_runner, RecruitmentState

    state: RecruitmentState = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "candidate_data": candidate_data,
        "job_data": job_data,
        "assessment_provider": assessment_provider,
        "audit_trail": []
    }
    return recruitment_graph_runner.execute(state)

