import json
import logging
import sys
import os
import math
from typing import List, Dict, Any, Tuple, cast
from sqlalchemy.orm import Session

# Add project root to sys.path to enable importing from AI package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from AI.llm import llm
except Exception:
    llm = None

from app.models import Candidate, Job, CandidateScore, Recommendation, InterviewQuestion, Resume
from app.services.matcher import calculate_match_score

logger = logging.getLogger(__name__)

# --- Pure-Python NLP Utilities for Semantic Matching ---
def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercased alphanumeric words."""
    if not text:
        return []
    import re
    return re.findall(r'\b\w+\b', text.lower())

def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """Calculates cosine similarity between two texts using a simple pure-Python TF-IDF bag of words."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0

    # Build vocabulary
    vocab = set(tokens1).union(set(tokens2))
    
    # TF representations (raw counts)
    tf1 = {word: tokens1.count(word) for word in vocab}
    tf2 = {word: tokens2.count(word) for word in vocab}
    
    # Compute cosine similarity
    dot_product = sum(tf1[word] * tf2[word] for word in vocab)
    magnitude1 = math.sqrt(sum(val**2 for val in tf1.values()))
    magnitude2 = math.sqrt(sum(val**2 for val in tf2.values()))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
        
    return dot_product / (magnitude1 * magnitude2)

# --- Service Helper Functions ---

def clean_llm_json(content: str) -> str:
    """Helper to remove markdown json blocks if returned by LLM."""
    content = content.replace("```json", "").replace("```", "").strip()
    return content

def get_llm_response(prompt: str) -> str:
    """Safely invokes the ChatGroq model and handles exceptions."""
    if llm is None:
        raise ValueError("ChatGroq LLM is not initialized.")
    try:
        response = llm.invoke(prompt)
        return str(response.content).strip()
    except Exception as e:
        logger.warning(f"LLM invocation failed: {str(e)}")
        raise e

# --- Extraction Helper Functions ---

def get_extracted_candidate_info(candidate: Candidate, db: Session) -> Dict[str, Any]:
    """Retrieves full candidate info by parsing raw resume text using LLM, or falling back to database fields."""
    resume_db = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.created_at.desc()).first()
    raw_text = resume_db.raw_text if resume_db else candidate.resume_text
    text = str(raw_text) if raw_text is not None else ""
    if text:
        try:
            from AI.resume_extractor import extract_candidate_info
            info = cast(Dict[str, Any], extract_candidate_info(text))
            if not info.get("name") or info.get("name") == "Not Available":
                info["name"] = candidate.name
            if not info.get("email") or info.get("email") == "Not Available":
                info["email"] = candidate.email
            if not info.get("skills"):
                info["skills"] = candidate.skills or []
            if not info.get("experience"):
                info["experience"] = candidate.experience
            if not info.get("education"):
                info["education"] = candidate.education
            return info
        except Exception:
            pass
            
    return {
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills or [],
        "experience": candidate.experience,
        "education": candidate.education,
        "projects": candidate.projects or [],
        "certifications": [],
        "achievements": [],
        "languages": ["English"],
        "soft_skills": [],
        "expected_ctc": "",
        "current_company": "",
        "employment_gap": False
    }

def get_extracted_job_info(job: Job) -> Dict[str, Any]:
    """Retrieves full job info."""
    return {
        "job_title": job.title,
        "description": job.description,
        "required_skills": job.requirements or [],
        "experience": job.experience_required,
        "salary_range": "",
        "notice_period": ""
    }

# --- 1. Candidate Scoring Service ---
def score_candidate(candidate_id: int, job_id: int, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job not found.")

    cand_info = get_extracted_candidate_info(candidate, db)
    job_info = get_extracted_job_info(job)

    from AI.scorer import calculate_enhanced_score
    score_details = calculate_enhanced_score(cand_info, job_info)
    
    # Save score to DB
    job_exp = int(cast(Any, job.experience_required)) if job.experience_required is not None else 0
    cand_exp = int(cast(Any, candidate.experience)) if candidate.experience is not None else 0
    exp_gap = max(0, job_exp - cand_exp)

    score_rec = db.query(CandidateScore).filter(
        CandidateScore.candidate_id == candidate_id, CandidateScore.job_id == job_id
    ).first()
    
    final_score = score_details.get("match_percentage", 0.0)
    recommendation = score_details.get("recommendation", "Under Review")
    
    if not score_rec:
        score_rec = CandidateScore(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=final_score,
            matched_skills=score_details.get("matched_skills", []),
            missing_skills=score_details.get("missing_skills", []),
            experience_gap=exp_gap
        )
        db.add(score_rec)
    else:
        score_rec_any = cast(Any, score_rec)
        score_rec_any.match_score = final_score
        score_rec_any.matched_skills = score_details.get("matched_skills", [])
        score_rec_any.missing_skills = score_details.get("missing_skills", [])
        score_rec_any.experience_gap = exp_gap
        
    db.commit()
    
    # Update recommendation table
    rec_rec = db.query(Recommendation).filter(
        Recommendation.candidate_id == candidate_id, Recommendation.job_id == job_id
    ).first()
    
    if not rec_rec:
        rec_rec = Recommendation(
            candidate_id=candidate_id,
            job_id=job_id,
            recommendation=recommendation,
            strengths=[f"Matched skills: {', '.join(score_details.get('matched_skills', [])[:3])}"] if score_details.get('matched_skills') else [],
            weaknesses=[f"Missing skills: {', '.join(score_details.get('missing_skills', [])[:3])}"] if score_details.get('missing_skills') else [],
            ai_summary=f"Automated evaluation score: {final_score}%"
        )
        db.add(rec_rec)
    else:
        rec_rec_any = cast(Any, rec_rec)
        rec_rec_any.recommendation = recommendation
        rec_rec_any.strengths = [f"Matched skills: {', '.join(score_details.get('matched_skills', [])[:3])}"] if score_details.get('matched_skills') else []
        rec_rec_any.weaknesses = [f"Missing skills: {', '.join(score_details.get('missing_skills', [])[:3])}"] if score_details.get('missing_skills') else []
        rec_rec_any.ai_summary = f"Automated evaluation score: {final_score}%"
        
    db.commit()
    
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "match_score": final_score,
        "details": score_details,
        "recommendation": recommendation
    }

# --- 2. AI Summary Service ---
def summarize_candidate(candidate_id: int, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise ValueError("Candidate not found.")

    cand_info = get_extracted_candidate_info(candidate, db)

    summary = ""
    if llm is not None:
        try:
            prompt = f"""
            Create a detailed AI Summary for the candidate:
            Name: {cand_info.get("name")}
            Experience: {cand_info.get("experience")}
            Skills: {', '.join(cand_info.get("skills", []))}
            Projects: {', '.join(cand_info.get("projects", []))}
            Education: {cand_info.get("education")}
            Certifications: {', '.join(cand_info.get("certifications", []))}
            Achievements: {', '.join(cand_info.get("achievements", []))}
            Soft Skills: {', '.join(cand_info.get("soft_skills", []))}
            Current Company: {cand_info.get("current_company")}

            Please output a detailed report structured exactly with these headers:
            **Experience & Profile Overview:** [Overview paragraph]
            **Key Strengths:** [Key strengths bullet points]
            **Primary Technical Skills:** [Primary technical skills]
            **Areas for Improvement:** [Areas for improvement]
            **Overall Suitability:** [Overall suitability for a standard engineering role]
            """
            summary = get_llm_response(prompt)
        except Exception:
            pass

    if not summary:
        # Fallback
        skills_str = ", ".join(cand_info.get("skills", [])) or "software engineering"
        strengths = f"Possesses {cand_info.get('experience')} of experience; strong technical foundation in {skills_str}."
        summary = (
            f"**Experience & Profile Overview:** Professional with {cand_info.get('experience')} of experience.\n"
            f"**Key Strengths:** {strengths}\n"
            f"**Primary Technical Skills:** {skills_str}\n"
            f"**Areas for Improvement:** Broaden domain expertise across large-scale distributed architectures.\n"
            f"**Overall Suitability:** Good suitability for modern technical and engineering roles."
        )

    cast(Any, candidate).ai_summary = summary
    db.commit()
    return {
        "candidate_id": candidate_id,
        "name": candidate.name,
        "ai_summary": summary
    }

# --- 3. Skill Gap Analysis Service ---
def analyze_skill_gap(candidate_id: int, job_id: int, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job not found.")

    cand_info = get_extracted_candidate_info(candidate, db)
    job_info = get_extracted_job_info(job)

    cand_skills = cand_info.get("skills", [])
    job_reqs = job_info.get("required_skills", [])

    from AI.scorer import calculate_enhanced_score
    score_details = calculate_enhanced_score(cand_info, job_info)
    
    missing = score_details.get("missing_skills", [])
    matched = score_details.get("matched_skills", [])

    recommended_courses = []
    suggested_path = []
    upskilling_recs = []

    if llm is not None:
        try:
            prompt = f"""
            Perform a skill gap analysis for candidate {cand_info.get("name")} for job title '{job.title}'.
            Candidate Skills: {', '.join(cand_skills)}
            Job Required Skills: {', '.join(job_reqs)}
            Missing Skills: {', '.join(missing)}

            Return ONLY a valid JSON:
            {{
                "recommended_courses": ["Course 1 on Coursera", "Course 2 on Udemy"],
                "suggested_path": ["Milestone 1: Learn X", "Milestone 2: Build Y project"],
                "upskilling_recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
            """
            res = get_llm_response(prompt)
            data = json.loads(clean_llm_json(res))
            recommended_courses = data.get("recommended_courses", [])
            suggested_path = data.get("suggested_path", [])
            upskilling_recs = data.get("upskilling_recommendations", [])
        except Exception:
            pass

    # Fallbacks if LLM not available or output is empty
    if not recommended_courses:
        for skill in missing[:3]:
            recommended_courses.append(f"Complete {skill} Professional Certificate on Coursera/Udemy")
        if not recommended_courses:
            recommended_courses.append("Advanced Software Architecture and Design Principles")

    if not suggested_path:
        suggested_path = [
            "Milestone 1: Read official documentation and build small local mockups",
            "Milestone 2: Integrate missing technologies into existing projects",
            "Milestone 3: Complete online course assessments and obtain certifications"
        ]

    if not upskilling_recs:
        for skill in missing[:2]:
            upskilling_recs.append(f"Implement a hands-on Github project featuring {skill}")
        upskilling_recs.append("Participate in relevant coding challenges and technical workshops")

    # Save gap report to CandidateScore
    score_rec = db.query(CandidateScore).filter(
        CandidateScore.candidate_id == candidate_id, CandidateScore.job_id == job_id
    ).first()
    
    report_data = {
        "matched_skills": matched,
        "missing_skills": missing,
        "recommended_courses": recommended_courses,
        "suggested_path": suggested_path,
        "upskilling_recommendations": upskilling_recs
    }

    job_exp = int(cast(Any, job.experience_required)) if job.experience_required is not None else 0
    cand_exp = int(cast(Any, candidate.experience)) if candidate.experience is not None else 0
    exp_gap = max(0, job_exp - cand_exp)

    if score_rec:
        cast(Any, score_rec).skill_gap_report = report_data
    else:
        score_rec = CandidateScore(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=score_details.get("match_percentage", 0.0),
            matched_skills=matched,
            missing_skills=missing,
            experience_gap=exp_gap,
            skill_gap_report=report_data
        )
        db.add(score_rec)
    db.commit()

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_gap": max(0, job.experience_required - candidate.experience),
        "recommendations": recommended_courses + upskilling_recs,
        "recommended_courses": recommended_courses,
        "suggested_path": suggested_path,
        "upskilling_recommendations": upskilling_recs
    }


# --- 4. Interview Question Generation Service ---
def generate_interview_questions(candidate_id: int, job_id: int, db: Session) -> List[InterviewQuestion]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job not found.")

    cand_info = get_extracted_candidate_info(candidate, db)

    questions_data = []
    if llm is not None:
        try:
            prompt = f"""
            You are a senior recruiter. Generate exactly 4 customized interview questions for {cand_info.get("name")} applying for '{job.title}'.
            Candidate Skills: {', '.join(cand_info.get("skills", []))}
            Candidate Projects: {', '.join(cand_info.get("projects", []))}
            Candidate Experience: {cand_info.get("experience")}

            You MUST generate exactly one question for each of the following categories:
            1. Technical (Deep dive into technical skills or architecture)
            2. HR (Cultural fit, expectations, career goals)
            3. Coding (Short algorithmic/design challenge question)
            4. Behavioral (Handling conflict, failure, or teamwork using STAR method)

            Return ONLY a valid JSON list of objects:
            [
               {{"question": "...", "expected_answer": "...", "category": "Technical"}},
               {{"question": "...", "expected_answer": "...", "category": "HR"}},
               {{"question": "...", "expected_answer": "...", "category": "Coding"}},
               {{"question": "...", "expected_answer": "...", "category": "Behavioral"}}
            ]
            """
            res = get_llm_response(prompt)
            questions_data = json.loads(clean_llm_json(res))
        except Exception as e:
            logger.warning(f"Failed to generate questions via LLM: {str(e)}")

    if not questions_data or len(questions_data) < 4:
        # Fallback question generation (ensuring all 4 categories exist)
        primary_skill = cand_info.get("skills", ["Software Engineering"])[0]
        
        questions_data = [
            {
                "question": f"Explain your experience working with {primary_skill}. What are some best practices or challenges you've faced?",
                "expected_answer": f"Should detail practical work with {primary_skill}, architectural considerations, and debugging strategies.",
                "category": "Technical"
            },
            {
                "question": "Why are you looking for a new opportunity and what interests you about our company?",
                "expected_answer": "Shows alignment with company culture, values, and long-term career growth aspirations.",
                "category": "HR"
            },
            {
                "question": f"How would you design a rate limiter middleware for a REST API using {primary_skill}? What datastores would you use?",
                "expected_answer": "Should mention Token Bucket or Sliding Window algorithm using Redis for in-memory tracking.",
                "category": "Coding"
            },
            {
                "question": "Describe a conflict you had with a team member on a project deadline. How did you resolve it?",
                "expected_answer": "Uses STAR method, focuses on communication, active listening, compromise, and project success.",
                "category": "Behavioral"
            }
        ]

    # Save generated questions to DB
    created_questions = []
    # Clear previously generated questions for this candidate/job to avoid bloating
    db.query(InterviewQuestion).filter(
        InterviewQuestion.candidate_id == candidate_id, InterviewQuestion.job_id == job_id
    ).delete()
    
    for q in questions_data:
        db_q = InterviewQuestion(
            candidate_id=candidate_id,
            job_id=job_id,
            question=q.get("question"),
            expected_answer=q.get("expected_answer"),
            category=q.get("category", "Technical")
        )
        db.add(db_q)
        created_questions.append(db_q)
    
    db.commit()
    for q in created_questions:
        db.refresh(q)
        
    return created_questions

# --- 5. Explainable Recommendations Service ---
def generate_explainable_recommendation(candidate_id: int, job_id: int, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job not found.")

    cand_info = get_extracted_candidate_info(candidate, db)
    job_info = get_extracted_job_info(job)

    from AI.scorer import calculate_enhanced_score
    score_details = calculate_enhanced_score(cand_info, job_info)
    
    match_score = score_details.get("match_percentage", 0.0)
    recommendation = score_details.get("recommendation", "Under Review")
    matched_skills = score_details.get("matched_skills", [])
    missing_skills = score_details.get("missing_skills", [])

    strengths = []
    weaknesses = []
    justification = ""

    if llm is not None:
        try:
            prompt = f"""
            You are a recruiting director. Write a detailed, explainable recommendation for candidate {cand_info.get("name")} for job '{job.title}'.
            Candidate Profile:
            - Experience: {cand_info.get("experience")}
            - Current Company: {cand_info.get("current_company")}
            - Expected Salary: {cand_info.get("expected_ctc")}
            - Notice Period: {candidate.notice_period or 'Not specified'}
            - Skills: {', '.join(cand_info.get("skills", []))}
            - Projects: {', '.join(cand_info.get("projects", []))}
            
            Match Score Details:
            - Total Score: {match_score}%
            - Matched Skills: {', '.join(matched_skills)}
            - Missing Skills: {', '.join(missing_skills)}

            Output ONLY a valid JSON:
            {{
                "recommendation": "Shortlist",
                "strengths": ["...", "..."],
                "weaknesses": ["...", "..."],
                "justification": "Detailed rationale incorporating notice period, skills overlap, and projects fit."
            }}
            """
            res = get_llm_response(prompt)
            data = json.loads(clean_llm_json(res))
            recommendation = data.get("recommendation", "Under Review")
            strengths = data.get("strengths", [])
            weaknesses = data.get("weaknesses", [])
            justification = data.get("justification", "")
        except Exception:
            pass

    if not justification:
        # Fallback logic
        justification = (
            f"Candidate {candidate.name} matches {len(matched_skills)} required skills with a total match score of {match_score}%. "
            f"Their notice period is {candidate.notice_period or 'not specified'} and expected salary is {cand_info.get('expected_ctc') or 'not specified'}."
        )
        strengths = [
            f"Strong fit in skills: {', '.join(matched_skills[:3])}",
            f"Has {cand_info.get('experience')} of experience."
        ]
        projects = cand_info.get("projects")
        if projects is not None:
            strengths.append(f"Relevant projects: {', '.join(cast(list, projects)[:2])}")
        
        weaknesses = []
        if missing_skills:
            weaknesses.append(f"Missing requirements: {', '.join(missing_skills[:2])}")
        if cand_info.get("employment_gap"):
            weaknesses.append("Has detected employment gaps.")

    # Save to recommendations table
    rec_db = db.query(Recommendation).filter(
        Recommendation.candidate_id == candidate_id, Recommendation.job_id == job_id
    ).first()

    if not rec_db:
        rec_db = Recommendation(
            candidate_id=candidate_id,
            job_id=job_id,
            recommendation=recommendation,
            strengths=strengths,
            weaknesses=weaknesses,
            ai_summary=justification
        )
        db.add(rec_db)
    else:
        rec_db_any = cast(Any, rec_db)
        rec_db_any.recommendation = recommendation
        rec_db_any.strengths = strengths
        rec_db_any.weaknesses = weaknesses
        rec_db_any.ai_summary = justification
        
    db.commit()

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "match_score": match_score,
        "recommendation": recommendation,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "justification": justification,
        "notice_period": candidate.notice_period,
        "missing_skills": missing_skills
    }
# --- 6. Semantic Matching Service ---
def calculate_semantic_matching(candidate_id: int, job_id: int, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or Job not found.")

    # Get resume raw text
    resume_db = db.query(Resume).filter(Resume.candidate_id == candidate_id).order_by(Resume.created_at.desc()).first()
    resume_text = resume_db.raw_text if resume_db else candidate.resume_text
    
    cand_skills = cast(List[str], candidate.skills) if candidate.skills is not None else []
    job_reqs = cast(List[str], job.requirements) if job.requirements is not None else []
 
    resume_text_str = str(resume_text) if resume_text is not None else ""
    if not resume_text_str:
        resume_text_str = f"Name: {candidate.name}. Skills: {', '.join(cand_skills)}."
 
    job_text = f"Title: {job.title}. Description: {job.description}. Requirements: {', '.join(job_reqs)}."

    # Call the new semantic matcher
    from app.services.semantic_matcher import match_resume_to_job_semantic, get_text_embedding
    
    resume_str = resume_text_str
    job_str = str(job_text)
    match_res = match_resume_to_job_semantic(resume_str, job_str)
    semantic_score = match_res.get("semantic_score", 0.0)
    
    highlights = []
    # Build highlights
    matched_skills = [str(s) for s in cand_skills if s in job_reqs]
    if matched_skills:
        highlights.append(f"Strong overlap in core skills: {', '.join(matched_skills[:3])}")
    
    job_exp = int(cast(Any, job.experience_required)) if job.experience_required is not None else 0
    cand_exp = int(cast(Any, candidate.experience)) if candidate.experience is not None else 0
    if cand_exp >= job_exp:
        highlights.append(f"Meets or exceeds the required experience level of {job_exp} years")
    else:
        highlights.append("Candidate possesses relevant technical background")

    # Generate and save real embedding representation
    emb = get_text_embedding(resume_str)
    if resume_db:
        cast(Any, resume_db).embedding = emb
        db.commit()

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "semantic_score": semantic_score,
        "matching_highlights": highlights
    }

