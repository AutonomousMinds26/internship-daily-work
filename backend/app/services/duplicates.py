import logging
from typing import Dict, Any, Optional, cast, List
from sqlalchemy.orm import Session

from app.models import Candidate, Resume
from app.services.semantic_matcher import get_text_embedding, compute_cosine_similarity

logger = logging.getLogger(__name__)

def check_duplicate_candidate(
    email: str,
    phone: Optional[str],
    resume_text: str,
    resume_hash: str,
    db: Session
) -> Dict[str, Any]:
    """
    Checks if a candidate resume submission is a duplicate based on:
    1. Exact SHA-256 File/Text Hash
    2. Email address matching
    3. Phone number matching (if provided)
    4. Resume Semantic Content Similarity (threshold > 90%)
    
    Returns:
        Dict: {"is_duplicate": bool, "reason": str, "duplicate_id": int, "name": str}
    """
    logger.info(f"Checking duplicates for submission: Email={email}, Phone={phone}")

    # 1. Check exact SHA-256 file text hash
    if resume_hash:
        dup_hash = db.query(Candidate).filter(Candidate.resume_hash == resume_hash).first()
        if dup_hash:
            logger.info(f"Duplicate found by exact text hash: Candidate ID {dup_hash.id}")
            return {
                "is_duplicate": True,
                "reason": "Exact file content match (duplicate hash).",
                "duplicate_id": dup_hash.id,
                "name": dup_hash.name
            }

    # 2. Check exact email address (case-insensitive)
    email_clean = email.strip().lower()
    dup_email = db.query(Candidate).filter(Candidate.email.ilike(email_clean)).first()
    if dup_email:
        logger.info(f"Duplicate found by email address: Candidate ID {dup_email.id}")
        return {
            "is_duplicate": True,
            "reason": "Email address matches an existing candidate.",
            "duplicate_id": dup_email.id,
            "name": dup_email.name
        }

    # 3. Check phone number (clean alphanumeric match)
    if phone:
        phone_digits = "".join(filter(str.isdigit, phone))
        if len(phone_digits) >= 7:
            # Retrieve all candidates and compare cleaned phone numbers
            all_candidates = db.query(Candidate).filter(Candidate.phone.isnot(None)).all()
            for cand in all_candidates:
                cand_phone_digits = "".join(filter(str.isdigit, str(cand.phone or "")))
                if cand_phone_digits == phone_digits:
                    logger.info(f"Duplicate found by phone number: Candidate ID {cand.id}")
                    return {
                        "is_duplicate": True,
                        "reason": "Phone number matches an existing candidate.",
                        "duplicate_id": cand.id,
                        "name": cand.name
                    }

    # 4. Check semantic content similarity (threshold >= 90%)
    if resume_text and len(resume_text.strip()) > 50:
        upload_emb = get_text_embedding(resume_text)
        
        # Load all existing candidates with resumes
        resumes = db.query(Resume).all()
        for res in resumes:
            res_text = str(res.raw_text or "")
            if len(res_text.strip()) > 50:
                # Get or compute embedding for comparison
                existing_emb = res.embedding
                if existing_emb is None:
                    existing_emb = get_text_embedding(res_text)
                    cast(Any, res).embedding = existing_emb
                    db.commit()
                
                # Compute cosine similarity
                similarity = compute_cosine_similarity(upload_emb, cast(List[float], existing_emb))
                if similarity >= 0.90:
                    cand = db.query(Candidate).filter(Candidate.id == res.candidate_id).first()
                    if cand:
                        logger.info(f"Duplicate found by semantic similarity ({round(similarity*100, 2)}%): Candidate ID {cand.id}")
                        return {
                            "is_duplicate": True,
                            "reason": f"Semantic similarity of {round(similarity*100, 2)}% exceeds duplicate threshold of 90%.",
                            "duplicate_id": cand.id,
                            "name": cand.name
                        }

    return {"is_duplicate": False}
