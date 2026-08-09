from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.auth import RoleChecker, User
from app.schemas import (
    ScoreResponse, AISummaryResponse, SkillGapResponse,
    InterviewQuestionsResponse, ExplainableRecommendationResponse, SemanticMatchResponse,
    ScreeningQuestionnaireResponse, ScreeningEvaluateRequest, ScreeningEvaluateResponse,
    FeedbackAnalysisRequest, FeedbackAnalysisResponse
)
from app.models import Candidate, Job, Interview
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

@router.post("/screening-questionnaire", response_model=ScreeningQuestionnaireResponse, status_code=status.HTTP_200_OK)
def run_screening_questionnaire(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Generate screening questionnaire focused on initial screening.
    """
    logger.info(f"AI Router: Generating Screening Questionnaire for Candidate {candidate_id} vs Job {job_id}")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    try:
        from AI.screening_questionnaire import generate_screening_questionnaire
        cand_dict = {
            "name": candidate.name,
            "skills": candidate.skills,
            "experience": candidate.experience,
            "projects": candidate.projects,
            "location": candidate.location,
            "notice_period": candidate.notice_period,
            "expected_ctc": candidate.expected_ctc,
            "resume_text": candidate.resume_text
        }
        job_dict = {
            "job_title": job.title,
            "required_skills": job.requirements,
            "experience": job.experience_required,
            "description": job.description
        }
        questions = generate_screening_questionnaire(cand_dict, job_dict)
        return questions
    except Exception as e:
        logger.error(f"Failed to generate screening questionnaire: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/evaluate-screening-response", response_model=ScreeningEvaluateResponse, status_code=status.HTTP_200_OK)
def run_screening_response_evaluation(
    eval_in: ScreeningEvaluateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Evaluate candidate's answer to a screening question and update candidate score.
    """
    logger.info(f"AI Router: Evaluating Screening response for Candidate {eval_in.candidate_id}")
    candidate = db.query(Candidate).filter(Candidate.id == eval_in.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    try:
        from AI.screening_evaluator import evaluate_answer, calculate_final_score
        cand_dict = {
            "name": candidate.name,
            "skills": candidate.skills,
            "experience": candidate.experience,
            "education": candidate.education,
            "resume_text": candidate.resume_text
        }
        evaluation = evaluate_answer(cand_dict, eval_in.question, eval_in.answer)
        
        # Calculate new Screening and Final Score
        screening_score = float(evaluation["score"]) * 10.0 # scale 0-10 to 0-100
        
        candidate.screening_score = screening_score
        candidate.final_score = calculate_final_score(
            screening_score=screening_score,
            ats_score=candidate.ats_score or 0.0,
            match_score=candidate.match_score or 0.0
        )
        
        # Sync to database score field (legacy compatibility)
        candidate.score = candidate.final_score
        
        db.commit()
        db.refresh(candidate)
        
        # Invalidate cache
        from app.routes.candidates import invalidate_candidate
        invalidate_candidate(candidate.id)

        
        return {
            "score": evaluation["score"],
            "relevance": evaluation["relevance"],
            "concerns": evaluation["concerns"],
            "explanation": evaluation["explanation"],
            "final_score": candidate.final_score
        }
    except Exception as e:
        logger.error(f"Failed to evaluate screening response: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/feedback-analysis", response_model=FeedbackAnalysisResponse, status_code=status.HTTP_200_OK)
def run_feedback_analysis(
    req: FeedbackAnalysisRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(recruiter_manager_checker)
):
    """
    Analyze recruiter/interviewer feedback comments.
    If feedbacks not provided in request, queries candidate scheduled interviews in DB.
    """
    logger.info(f"AI Router: Running Feedback Analysis for Candidate {req.candidate_id}")
    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        
    feedbacks = req.feedbacks
    if not feedbacks:
        # Query interviews notes for this candidate
        interviews = db.query(Interview).filter(Interview.candidate_id == req.candidate_id).all()
        feedbacks = []
        for iv in interviews:
            if iv.notes and iv.notes.strip():
                feedbacks.append({
                    "interviewer": iv.interviewer_name,
                    "comment": iv.notes
                })
        
    if not feedbacks:
        # Standard fallback if absolutely no comments found
        feedbacks = [
            "Candidate has applied. No interview comments found in candidate history notes."
        ]

    try:
        from AI.feedback_analyzer import analyze_feedback
        analysis = analyze_feedback(feedbacks)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze feedback: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

