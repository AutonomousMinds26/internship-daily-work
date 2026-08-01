from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.auth import RoleChecker, User
from app.schemas import (
    ScoreResponse, AISummaryResponse, SkillGapResponse,
    InterviewQuestionsResponse, ExplainableRecommendationResponse, SemanticMatchResponse
)
from app.services import ai_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

# RBAC: Only Recruiters, Hiring Managers, and Admins can trigger AI pipeline integrations
recruiter_manager_checker = RoleChecker(allowed_roles=["Recruiter", "Hiring Manager", "Admin"])

@router.post("/score", response_model=dict, status_code=status.HTTP_200_OK)
def run_candidate_scoring(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Trigger Candidate Scoring against a Job ID. Refines compatibility based on LLM/python rules.
    """
    logger.info(f"AI Router: Scoring Candidate {candidate_id} against Job {job_id}")
    try:
        result = ai_pipeline.score_candidate(candidate_id, job_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to score candidate: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/summary", response_model=AISummaryResponse, status_code=status.HTTP_200_OK)
def run_candidate_summary(
    candidate_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Generate an AI Profile Summary for a candidate and save it in the database.
    """
    logger.info(f"AI Router: Summarizing Candidate {candidate_id}")
    try:
        result = ai_pipeline.summarize_candidate(candidate_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to summarize candidate: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/skill-gap", response_model=SkillGapResponse, status_code=status.HTTP_200_OK)
def run_skill_gap_analysis(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Run detailed Skill Gap Analysis identifying matches, gaps, and recommendations.
    """
    logger.info(f"AI Router: Analyzing Skill Gap for Candidate {candidate_id} vs Job {job_id}")
    try:
        result = ai_pipeline.analyze_skill_gap(candidate_id, job_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run skill gap analysis: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/interview-questions", response_model=InterviewQuestionsResponse, status_code=status.HTTP_200_OK)
def run_interview_question_generation(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Generate technical & behavioral interview questions tailored to candidate profile and job.
    """
    logger.info(f"AI Router: Generating Interview Questions for Candidate {candidate_id} vs Job {job_id}")
    try:
        db_questions = ai_pipeline.generate_interview_questions(candidate_id, job_id, db)
        return {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "questions": db_questions
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate interview questions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/recommendation", response_model=ExplainableRecommendationResponse, status_code=status.HTTP_200_OK)
def run_explainable_recommendation(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Get explainable recruiter fit recommendations with highlights on strengths and weaknesses.
    """
    logger.info(f"AI Router: Generating fit recommendation for Candidate {candidate_id} vs Job {job_id}")
    try:
        result = ai_pipeline.generate_explainable_recommendation(candidate_id, job_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate fit recommendation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/semantic-match", response_model=SemanticMatchResponse, status_code=status.HTTP_200_OK)
def run_semantic_matching(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Calculate semantic similarity score between candidate resume/skills and job requirements.
    """
    logger.info(f"AI Router: Running Semantic Match for Candidate {candidate_id} vs Job {job_id}")
    try:
        result = ai_pipeline.calculate_semantic_matching(candidate_id, job_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate semantic match: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
