import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import (
    Candidate, Job, Resume, CandidateScore, Assessment,
    Verification, CandidateActivity, DailyAnalyticsMetric
)
from app.services.sourcing_service import calculate_ats_and_match
from app.services.assessment_integration import AssessmentIntegrationManager
from app.services.email_service import send_email_notification
from app.services.verification_service import submit_background_verification

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_resume_task(self, candidate_id: int, raw_text: str, filename: str = "") -> Dict[str, Any]:
    """
    Asynchronous Celery task for processing and indexing candidate resumes.
    Computes text parsing, ATS metrics, and embeddings.
    """
    logger.info(f"[Celery Task] Starting process_resume_task for candidate_id={candidate_id}")
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            logger.error(f"Candidate with id {candidate_id} not found.")
            return {"success": False, "error": "Candidate not found"}

        # Simulate vector embedding computation
        import hashlib
        words = raw_text.split()
        embedding = [float(int(hashlib.md5(w.encode()).hexdigest(), 16) % 100) / 100.0 for w in words[:32]]
        if len(embedding) < 32:
            embedding += [0.0] * (32 - len(embedding))

        # Check existing resume record
        resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
        if not resume:
            resume = Resume(
                candidate_id=candidate_id,
                file_name=filename or "uploaded_resume.txt",
                file_type="txt",
                raw_text=raw_text,
                parsed_data={"word_count": len(words), "char_count": len(raw_text)},
                embedding=embedding
            )
            db.add(resume)
        else:
            resume.raw_text = raw_text
            resume.embedding = embedding

        # Log Activity
        activity = CandidateActivity(
            candidate_id=candidate_id,
            activity_type="resume_processed",
            description=f"Resume '{filename}' parsed and vector embeddings indexed asynchronously.",
            created_by="Celery Worker"
        )
        db.add(activity)
        db.commit()

        logger.info(f"[Celery Task] Successfully processed resume for candidate {candidate_id}")
        return {"success": True, "candidate_id": candidate_id, "word_count": len(words)}

    except Exception as exc:
        logger.error(f"[Celery Task] process_resume_task failed: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def bulk_screening_task(self, job_id: int, candidate_ids: List[int]) -> Dict[str, Any]:
    """
    Asynchronous Celery task for batch AI screening and matching against a Job.
    """
    logger.info(f"[Celery Task] Starting bulk_screening_task for job_id={job_id} with {len(candidate_ids)} candidates")
    db = SessionLocal()
    results = []
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"success": False, "error": "Job not found"}

        for cand_id in candidate_ids:
            candidate = db.query(Candidate).filter(Candidate.id == cand_id).first()
            if not candidate:
                continue

            # Run ATS and Match Score
            job_dict = {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "required_skills": job.requirements or [],
                "experience": job.experience_required or 0
            }
            cand_dict = {
                "id": candidate.id,
                "name": candidate.name,
                "skills": candidate.skills or [],
                "experience": candidate.experience or 0,
                "education": candidate.education or "",
                "resume_text": candidate.resume_text or ""
            }

            score_data = calculate_ats_and_match(cand_dict, job_dict)
            candidate.ats_score = score_data.get("ats_score", 0.0)
            candidate.match_score = score_data.get("match_score", 0.0)
            candidate.screening_score = score_data.get("screening_score", 0.0)
            candidate.final_score = score_data.get("final_score", 0.0)
            candidate.ats_details = score_data.get("ats_details", {})

            # Update or create CandidateScore
            cand_score = db.query(CandidateScore).filter(
                CandidateScore.candidate_id == cand_id,
                CandidateScore.job_id == job_id
            ).first()
            if not cand_score:
                cand_score = CandidateScore(
                    candidate_id=cand_id,
                    job_id=job_id,
                    match_score=score_data.get("match_score", 0.0),
                    matched_skills=score_data.get("matched_skills", []),
                    missing_skills=score_data.get("missing_skills", []),
                    experience_gap=score_data.get("experience_gap", 0)
                )
                db.add(cand_score)
            else:
                cand_score.match_score = score_data.get("match_score", 0.0)
                cand_score.matched_skills = score_data.get("matched_skills", [])
                cand_score.missing_skills = score_data.get("missing_skills", [])

            results.append({"candidate_id": cand_id, "score": candidate.final_score})

        db.commit()
        logger.info(f"[Celery Task] Bulk screening completed for {len(results)} candidates")
        return {"success": True, "job_id": job_id, "screened_count": len(results), "results": results}

    except Exception as exc:
        logger.error(f"[Celery Task] bulk_screening_task failed: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_assessment_task(self, candidate_id: int, provider: str, test_name: str) -> Dict[str, Any]:
    """
    Asynchronous Celery task to dispatch an assessment invite to an external provider.
    """
    logger.info(f"[Celery Task] Dispatching assessment invite for candidate_id={candidate_id} via {provider}")
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}

        mgr = AssessmentIntegrationManager()
        client = mgr.get_client_by_provider(provider)
        res = client.invite_candidate(email=str(candidate.email), test_name=test_name)

        # Record in DB
        assessment = Assessment(
            candidate_id=candidate_id,
            assessment_provider=provider,
            test_name=test_name,
            status="Pending",
            report_url=res.get("invite_url")
        )
        db.add(assessment)

        activity = CandidateActivity(
            candidate_id=candidate_id,
            activity_type="assessment_dispatched",
            description=f"Assessment '{test_name}' dispatched via {provider}. Invite: {res.get('invite_url')}",
            created_by="Celery Worker"
        )
        db.add(activity)
        db.commit()

        return {"success": True, "assessment_id": assessment.id, "provider": provider}

    except Exception as exc:
        logger.error(f"[Celery Task] send_assessment_task failed: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_notification_email_task(
    self,
    recipient_email: str,
    subject: str,
    body: str,
    candidate_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Asynchronous Celery task for transactional email delivery.
    """
    logger.info(f"[Celery Task] Sending notification email to {recipient_email}")
    try:
        result = send_email_notification(recipient=recipient_email, subject=subject, content=body)
        if candidate_id:
            db = SessionLocal()
            try:
                activity = CandidateActivity(
                    candidate_id=candidate_id,
                    activity_type="email_dispatched",
                    description=f"Email sent to {recipient_email}: '{subject}'",
                    created_by="Celery Email Worker"
                )
                db.add(activity)
                db.commit()
            finally:
                db.close()
        return result
    except Exception as exc:
        logger.error(f"[Celery Task] send_notification_email_task failed: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def run_background_verification_task(
    self,
    candidate_id: int,
    verification_type: str,
    agency: str = "Checkr"
) -> Dict[str, Any]:
    """
    Asynchronous Celery task for initiating candidate background checks.
    """
    logger.info(f"[Celery Task] Running background verification for candidate_id={candidate_id} via {agency}")
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}

        res = submit_background_verification(
            candidate_id=candidate.id,
            candidate_name=str(candidate.name),
            candidate_email=str(candidate.email),
            verification_type=verification_type,
            agency=agency
        )

        verif = Verification(
            candidate_id=candidate_id,
            verification_type=verification_type,
            agency=agency,
            status=res.get("status", "Pending"),
            details=res.get("message", "Verification in progress")
        )
        db.add(verif)

        activity = CandidateActivity(
            candidate_id=candidate_id,
            activity_type="verification_initiated",
            description=f"{verification_type} check initiated with {agency}. Ref: {res.get('external_id')}",
            created_by="Celery Worker"
        )
        db.add(activity)
        db.commit()

        return {"success": True, "verification_id": verif.id, "external_id": res.get("external_id")}

    except Exception as exc:
        logger.error(f"[Celery Task] run_background_verification_task failed: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task
def aggregate_analytics_daily_task(metric_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Asynchronous Celery task to aggregate daily recruitment funnel metrics.
    """
    if not metric_date:
        metric_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    logger.info(f"[Celery Task] Aggregating recruitment metrics for date: {metric_date}")
    db = SessionLocal()
    try:
        total_candidates = db.query(Candidate).filter(Candidate.is_deleted == False).count()
        applied = db.query(Candidate).filter(Candidate.status == "Applied").count()
        screened = db.query(Candidate).filter(Candidate.status == "Screened").count()
        interviewed = db.query(Candidate).filter(Candidate.status.in_(["Interview", "Interview Scheduled"])).count()
        offered = db.query(Candidate).filter(Candidate.status == "Offered").count()
        hired = db.query(Candidate).filter(Candidate.status.in_(["Hired", "Selected"])).count()

        metrics = [
            ("total_candidates", float(total_candidates)),
            ("applied_count", float(applied)),
            ("screened_count", float(screened)),
            ("interviewed_count", float(interviewed)),
            ("offered_count", float(offered)),
            ("hired_count", float(hired)),
        ]

        for m_name, m_val in metrics:
            rec = db.query(DailyAnalyticsMetric).filter(
                DailyAnalyticsMetric.metric_date == metric_date,
                DailyAnalyticsMetric.metric_name == m_name
            ).first()
            if not rec:
                rec = DailyAnalyticsMetric(metric_date=metric_date, metric_name=m_name, metric_value=m_val)
                db.add(rec)
            else:
                rec.metric_value = m_val

        db.commit()
        return {"success": True, "date": metric_date, "total_candidates": total_candidates}
    except Exception as exc:
        logger.error(f"[Celery Task] aggregate_analytics_daily_task error: {str(exc)}")
        db.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        db.close()
