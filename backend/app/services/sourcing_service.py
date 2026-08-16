import logging
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Candidate, Job, CandidateSource, CandidateActivity
from app.services.duplicates import check_duplicate_candidate
from app.services import ai_pipeline
from AI.ats_analyzer import analyze_ats

logger = logging.getLogger(__name__)

def import_candidate_from_source(
    candidate_data: Dict[str, Any],
    source_data: Dict[str, Any],
    job_id: Optional[int],
    db: Session,
    performed_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Candidate Sourcing Flow:
    External Source -> Backend -> Duplicate Check -> Candidate DB -> AI Screening
    """
    email = str(candidate_data.get("email") or "")
    phone = candidate_data.get("phone")
    resume_text = candidate_data.get("resume_text") or ""
    
    # 1. Duplicate Check
    resume_hash = hashlib.sha256(resume_text.encode("utf-8")).hexdigest() if resume_text else ""
    
    logger.info(f"Sourcing candidate duplicate check for {email}")
    dup_res = check_duplicate_candidate(
        email=email,
        phone=phone,
        resume_text=resume_text,
        resume_hash=resume_hash,
        db=db
    )
    
    if dup_res["is_duplicate"]:
        logger.warning(f"Sourced candidate duplicate detected: {dup_res['reason']}")
        return {
            "is_duplicate": True,
            "duplicate_details": dup_res,
            "candidate": None
        }

    # 2. Get Job for AI Screening
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
    else:
        job = db.query(Job).first()
        
    if not job:
        # Fallback default job
        logger.info("No Job found. Creating fallback job for screening.")
        job = Job(
            title="Software Engineer",
            description="Fallback software engineer JD.",
            requirements=["Python", "SQL"],
            experience_required=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    
    # 3. Create Candidate in Candidate DB
    logger.info(f"Creating sourced candidate record: {email}")
    skills_list = candidate_data.get("skills", [])
    if isinstance(skills_list, str):
        skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]
        
    projects_list = candidate_data.get("projects", [])
    if isinstance(projects_list, str):
        projects_list = [p.strip() for p in projects_list.split(",") if p.strip()]

    # Extract years of experience
    exp_val = candidate_data.get("experience", 0)
    try:
        experience_years = int(exp_val)
    except ValueError:
        import re
        match = re.search(r'(\d+)', str(exp_val))
        experience_years = int(match.group(1)) if match else 0

    candidate_db = Candidate(
        name=candidate_data.get("name"),
        email=email,
        phone=phone,
        education=candidate_data.get("education"),
        experience=experience_years,
        skills=skills_list,
        projects=projects_list,
        notice_period=candidate_data.get("notice_period"),
        expected_ctc=candidate_data.get("expected_ctc"),
        location=candidate_data.get("location"),
        resume_text=resume_text,
        status="Applied",
        resume_hash=resume_hash if resume_hash else None
    )
    db.add(candidate_db)
    db.commit()
    db.refresh(candidate_db)

    # 4. Link CandidateSource
    logger.info(f"Linking candidate {candidate_db.id} to source {source_data.get('source_name')}")
    cand_source = CandidateSource(
        candidate_id=candidate_db.id,
        source_name=source_data.get("source_name"),
        source_type=source_data.get("source_type"),
        external_candidate_id=source_data.get("external_candidate_id"),
        sourcing_payload=source_data.get("sourcing_payload")
    )
    db.add(cand_source)
    
    # Log Sourced Activity
    activity = CandidateActivity(
        candidate_id=candidate_db.id,
        activity_type="candidate_sourced",
        description=f"Candidate successfully sourced from {source_data.get('source_name')} ({source_data.get('source_type')})",
        created_by=performed_by or "system"
    )
    db.add(activity)
    db.commit()

    # 5. Run AI Screening
    logger.info(f"Running AI Screening for sourced candidate {candidate_db.id} against job {job.id}")
    try:
        # Run AI matching and scoring
        score_res = ai_pipeline.score_candidate(int(candidate_db.id), int(job.id), db)
        match_score = score_res.get("match_score", 0.0)
        
        # Generate summary
        ai_pipeline.summarize_candidate(int(candidate_db.id), db)
        
        # Generate skill gap
        ai_pipeline.analyze_skill_gap(int(candidate_db.id), int(job.id), db)
        
        # Generate interview questions
        ai_pipeline.generate_interview_questions(int(candidate_db.id), int(job.id), db)
        
        # Generate explainable recommendation
        ai_pipeline.generate_explainable_recommendation(int(candidate_db.id), int(job.id), db)
        
        # Calculate ATS details & score
        cand_dict_ats = {
            "name": candidate_db.name,
            "email": candidate_db.email,
            "phone": candidate_db.phone,
            "skills": skills_list,
            "experience": experience_years,
            "education": candidate_db.education,
            "projects": projects_list,
            "resume_text": resume_text
        }
        job_info_ats = {
            "job_title": job.title,
            "required_skills": job.requirements or [],
            "experience": f"{job.experience_required} years",
            "location": "",
            "salary_range": "",
            "notice_period": ""
        }
        
        ats_res = analyze_ats(cand_dict_ats, job_info_ats)
        ats_score = float(ats_res.get("ats_score", 0.0))
        
        # Calculate screening score
        screening_score = 0.0
        if experience_years >= (job.experience_required or 0):
            screening_score += 40
        elif (job.experience_required or 0) - experience_years <= 1:
            screening_score += 30
        elif (job.experience_required or 0) - experience_years <= 2:
            screening_score += 20
        else:
            screening_score += 10
            
        job_skills_norm = {s.lower().strip() for s in (job.requirements or [])}
        cand_skills_norm = {s.lower().strip() for s in skills_list}
        matched_skills_count = len(job_skills_norm & cand_skills_norm)
        if job_skills_norm:
            skills_ratio = matched_skills_count / len(job_skills_norm)
            screening_score += (skills_ratio * 40)
        else:
            screening_score += 40
            
        edu_lower = str(candidate_db.education or "").lower()
        if any(kw in edu_lower for kw in ["ph.d", "doctor", "master", "m.tech", "mca"]):
            screening_score += 20
        elif any(kw in edu_lower for kw in ["b.tech", "b.e", "bachelor", "bsc", "bca"]):
            screening_score += 15
        else:
            screening_score += 10
            
        final_score = round((0.3 * ats_score) + (0.5 * match_score) + (0.2 * screening_score), 2)
        
        # Save final scores back to candidate DB
        setattr(candidate_db, "ats_score", ats_score)
        setattr(candidate_db, "match_score", match_score)
        setattr(candidate_db, "screening_score", screening_score)
        setattr(candidate_db, "final_score", final_score)
        setattr(candidate_db, "ats_details", ats_res)
        
        # Log Screening Completed Activity
        screen_activity = CandidateActivity(
            candidate_id=int(candidate_db.id),
            activity_type="ai_screening_completed",
            description=f"AI screening completed with composite score of {final_score}%",
            created_by="system"
        )
        db.add(screen_activity)
        db.commit()
        db.refresh(candidate_db)
        
    except Exception as e:
        logger.error(f"AI screening failed for sourced candidate {candidate_db.id}: {str(e)}", exc_info=True)
        # Log failure activity but preserve candidate record
        fail_activity = CandidateActivity(
            candidate_id=int(candidate_db.id),
            activity_type="ai_screening_failed",
            description=f"AI screening failed: {str(e)}",
            created_by="system"
        )
        db.add(fail_activity)
        db.commit()

    return {
        "is_duplicate": False,
        "duplicate_details": None,
        "candidate": candidate_db
    }
