import pytest
from AI.workflow import app_graph
from AI.scorer import calculate_enhanced_score
from app.services.duplicates import check_duplicate_candidate
from app.services.semantic_matcher import match_resume_to_job_semantic, get_text_embedding, compute_cosine_similarity
from app.models import Candidate, Job, Resume, CandidateScore, Recommendation, InterviewQuestion

def test_workflow_invoke(client, db):
    # Setup job
    job = Job(
        title="Backend Software Engineer",
        description="Write high performance APIs using Python, FastAPI, and SQL.",
        requirements=["Python", "FastAPI", "SQL"],
        experience_required=3
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Setup candidate
    candidate = Candidate(
        name="Bob Martin",
        email="bob.martin@example.com",
        phone="+1234567890",
        skills=["Python", "SQL"],
        experience=4,
        education="Master's in Software Engineering",
        projects=["Built a FastAPI inventory microservice", "Created SQLite database wrapper"],
        notice_period="15 days"
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Setup resume raw text
    resume = Resume(
        candidate_id=candidate.id,
        file_name="resume.txt",
        file_type="text/plain",
        raw_text=(
            "Bob Martin\n"
            "Email: bob.martin@example.com\n"
            "Phone: +1234567890\n"
            "Skills: Python, SQL\n"
            "Experience: 4 years\n"
            "Education: Master's in Software Engineering\n"
            "Projects: Built a FastAPI inventory microservice, Created SQLite database wrapper\n"
            "Certifications: AWS Certified Developer\n"
            "Achievements: Top Developer Award\n"
            "Languages: English, Spanish\n"
            "Soft Skills: Leadership, Communication\n"
            "Expected Salary: 10 LPA\n"
            "Current Company: Tech Corp\n"
            "Employment Gap: No\n"
        )
    )
    db.add(resume)
    db.commit()

    # Invoke Workflow
    inputs = {
        "file_path": "dummy_resume.txt",
        "resume_text": resume.raw_text,
        "job_text": job.description,
        "candidate_id": candidate.id,
        "job_id": job.id,
        "db": db
    }
    
    result = app_graph.invoke(inputs)
    
    assert "candidate_data" in result
    assert "job_data" in result
    assert "score_details" in result
    assert "recommendation_details" in result
    assert result["score_details"]["match_percentage"] > 0.0

def test_enhanced_scoring_logic():
    candidate = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "skills": ["Python", "FastAPI"],
        "experience": "5 years",
        "education": "Ph.D. in Computer Science",
        "projects": ["Project A", "Project B"],
        "certifications": ["AWS Solutions Architect"],
        "achievements": ["Best Paper Award"],
        "languages": ["English", "French"],
        "soft_skills": ["Leadership", "Mentoring"],
        "expected_ctc": "15 LPA",
        "current_company": "Innovative Inc",
        "employment_gap": False
    }
    
    job = {
        "job_title": "Senior Python Architect",
        "required_skills": ["Python", "FastAPI", "Docker"],
        "experience": 4,
        "salary_range": "10-20 LPA"
    }

    score_details = calculate_enhanced_score(candidate, job)
    
    assert score_details["skills_score"] > 0
    assert score_details["experience_score"] == 15.0
    assert score_details["education_score"] == 10.0
    assert score_details["project_score"] > 0
    assert score_details["certification_score"] == 5.0
    assert score_details["achievements_score"] == 5.0
    assert score_details["languages_score"] == 5.0
    assert score_details["soft_skills_score"] == 5.0
    assert score_details["salary_score"] == 5.0
    assert score_details["current_company_score"] == 5.0
    assert score_details["employment_gap_score"] == 5.0
    assert score_details["match_percentage"] > 50.0

def test_semantic_matcher_fallback():
    resume_text = "Experienced software engineer with deep Python and FastAPI capabilities."
    job_text = "Looking for a developer skilled in Python API development using FastAPI."
    
    match_res = match_resume_to_job_semantic(resume_text, job_text)
    assert "semantic_score" in match_res
    assert match_res["semantic_score"] >= 0.0
    
    # Check vector dimension
    emb = get_text_embedding(resume_text)
    assert len(emb) == 128 or len(emb) == 384

def test_duplicate_candidate_detection(db):
    # Setup first candidate
    c1 = Candidate(
        name="Dup Candidate",
        email="dup@example.com",
        phone="555-1234",
        skills=["Python"],
        experience=2
    )
    db.add(c1)
    db.commit()
    
    r1 = Resume(
        candidate_id=c1.id,
        file_name="resume.txt",
        file_type="text/plain",
        raw_text="Dup Candidate profile description with software engineering experience in Python."
    )
    db.add(r1)
    db.commit()
    
    # Test 1: exact email match
    res_email = check_duplicate_candidate(
        email="dup@example.com",
        phone=None,
        resume_text="",
        resume_hash="some-hash",
        db=db
    )
    assert res_email["is_duplicate"] is True
    assert "Email" in res_email["reason"]
    
    # Test 2: exact phone match
    res_phone = check_duplicate_candidate(
        email="other@example.com",
        phone="555-1234",
        resume_text="",
        resume_hash="some-hash",
        db=db
    )
    assert res_phone["is_duplicate"] is True
    assert "Phone" in res_phone["reason"]

    # Test 3: semantic similarity match (>90%)
    res_semantic = check_duplicate_candidate(
        email="other@example.com",
        phone="999-9999",
        resume_text="Dup Candidate profile description with software engineering experience in Python.",
        resume_hash="other-hash",
        db=db
    )
    assert res_semantic["is_duplicate"] is True
    assert "similarity" in res_semantic["reason"].lower()
