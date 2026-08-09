import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.logging_config import setup_logging
from app.models import User, Candidate
from app.auth import get_password_hash
from app.routes import auth, jobs, candidates, interviews, communication

# Initialize logging configuration
setup_logging()
logger = logging.getLogger(__name__)

def seed_users():
    """Seed default test users if they don't already exist."""
    db = SessionLocal()
    try:
        users = [
            ("admin_user", "Admin"),
            ("recruiter_user", "Recruiter"),
            ("manager_user", "Hiring Manager"),
            ("alice.smith@example.com", "Candidate")
        ]
        for username, role in users:
            existing_user = db.query(User).filter(User.username == username).first()
            if not existing_user:
                logger.info(f"Seeding user '{username}' with role '{role}'")
                password_hash = get_password_hash("password123")
                user = User(
                    username=username,
                    password_hash=password_hash,
                    role=role
                )
                db.add(user)
        db.commit()
    except Exception as e:
        logger.error(f"Seeding users failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

def seed_candidates():
    """Seed 50 candidates if DB contains fewer candidates to satisfy A2-9 requirements."""
    db = SessionLocal()
    try:
        count = db.query(Candidate).count()
        if count >= 50:
            return

        logger.info("Seeding candidate dataset to reach 50 candidates...")
        
        # Specified named candidates from prompt:
        # Applied: Rahul, Rohan
        # Screening: Ananya, Sneha
        # Interview: Priya
        # Selected: Amit
        prompt_candidates = [
            # Applied (4 total)
            {"name": "Rahul Sharma", "email": "rahul.sharma@example.com", "phone": "+91 98765 43210", "status": "Applied", "experience": 3, "education": "B.Tech Computer Science", "skills": ["Python", "FastAPI", "Docker"], "ats_score": 88, "screening_score": 82, "final_score": 84, "ai_recommendation": "Shortlist for technical assessment.", "candidate_summary": "Python developer with experience in building REST APIs and microservices."},
            {"name": "Rohan Verma", "email": "rohan.verma@example.com", "phone": "+91 98765 43211", "status": "Applied", "experience": 2, "education": "B.Sc Information Technology", "skills": ["React", "JavaScript", "Node.js"], "ats_score": 82, "screening_score": 78, "final_score": 80, "ai_recommendation": "Good candidate for frontend role.", "candidate_summary": "Frontend developer focused on modern web UI component design."},
            {"name": "Vikas Kumar", "email": "vikas.kumar@example.com", "phone": "+91 98765 43212", "status": "Applied", "experience": 4, "education": "B.Tech Electronics", "skills": ["Python", "Django", "PostgreSQL"], "ats_score": 85, "screening_score": 80, "final_score": 82, "ai_recommendation": "Under Review.", "candidate_summary": "Backend specialist working with Django and SQL databases."},
            {"name": "Kavita Reddy", "email": "kavita.reddy@example.com", "phone": "+91 98765 43213", "status": "Applied", "experience": 1, "education": "B.Tech Computer Science", "skills": ["Java", "Spring Boot", "MySQL"], "ats_score": 79, "screening_score": 75, "final_score": 77, "ai_recommendation": "Junior potential candidate.", "candidate_summary": "Recent graduate with strong Java OOP fundamentals."},

            # Screening (3 total)
            {"name": "Ananya Roy", "email": "ananya.roy@example.com", "phone": "+91 98765 43214", "status": "Screening", "experience": 5, "education": "M.Tech Data Science", "skills": ["Python", "LLM", "PyTorch", "NLP"], "ats_score": 93, "screening_score": 89, "final_score": 91, "ai_recommendation": "Strong Match for AI Engineer position.", "candidate_summary": "Experienced Data Scientist specializing in Large Language Models."},
            {"name": "Sneha Gupta", "email": "sneha.gupta@example.com", "phone": "+91 98765 43215", "status": "Screening", "experience": 4, "education": "B.Tech Computer Science", "skills": ["React", "TypeScript", "Next.js", "TailwindCSS"], "ats_score": 90, "screening_score": 86, "final_score": 88, "ai_recommendation": "Highly suitable for Senior Frontend Lead.", "candidate_summary": "Frontend architect with expertise in modern web user experience."},
            {"name": "Manish Patel", "email": "manish.patel@example.com", "phone": "+91 98765 43216", "status": "Screening", "experience": 6, "education": "B.E. Information Technology", "skills": ["Go", "Kubernetes", "Docker", "AWS"], "ats_score": 89, "screening_score": 87, "final_score": 88, "ai_recommendation": "DevOps & Cloud Engineer candidate.", "candidate_summary": "Cloud infrastructure engineer with automated CI/CD pipeline skills."},

            # Interview (8 total)
            {"name": "Priya Nair", "email": "priya.nair@example.com", "phone": "+91 98765 43217", "status": "Interview", "experience": 6, "education": "M.Tech Computer Science", "skills": ["Python", "FastAPI", "SQL", "Docker", "System Design"], "ats_score": 91, "screening_score": 84, "final_score": 88, "ai_recommendation": "Highly Recommended for Final Interview Round.", "candidate_summary": "Full Stack & System Architect candidate with 6 years experience in distributed systems."},
            {"name": "Siddharth Das", "email": "siddharth.das@example.com", "phone": "+91 98765 43218", "status": "Interview", "experience": 5, "education": "B.Tech Computer Science", "skills": ["Python", "LangChain", "OpenAI", "FastAPI"], "ats_score": 92, "screening_score": 88, "final_score": 90, "ai_recommendation": "Proceed to Technical Interview.", "candidate_summary": "Generative AI Application Developer."},
            {"name": "Deepak Mehta", "email": "deepak.mehta@example.com", "phone": "+91 98765 43219", "status": "Interview", "experience": 7, "education": "B.Tech Computer Science", "skills": ["Java", "Spring Cloud", "Kafka", "Microservices"], "ats_score": 89, "screening_score": 85, "final_score": 87, "ai_recommendation": "Senior Backend Candidate.", "candidate_summary": "Enterprise backend engineer with high-throughput event processing experience."},
            {"name": "Neha Joshi", "email": "neha.joshi@example.com", "phone": "+91 98765 43220", "status": "Interview", "experience": 4, "education": "M.Sc Computer Application", "skills": ["React Native", "Flutter", "iOS", "Android"], "ats_score": 87, "screening_score": 83, "final_score": 85, "ai_recommendation": "Mobile Engineer Lead candidate.", "candidate_summary": "Cross-platform mobile developer."},
            {"name": "Arjun Rao", "email": "arjun.rao@example.com", "phone": "+91 98765 43221", "status": "Interview", "experience": 8, "education": "B.Tech Computer Science", "skills": ["Python", "FastAPI", "AWS", "Terraform", "PostgreSQL"], "ats_score": 94, "screening_score": 90, "final_score": 92, "ai_recommendation": "Lead Engineer candidate.", "candidate_summary": "Senior engineering leader with cloud architecture background."},
            {"name": "Divya Saxena", "email": "divya.saxena@example.com", "phone": "+91 98765 43222", "status": "Interview", "experience": 5, "education": "B.Tech Information Technology", "skills": ["Node.js", "GraphQL", "MongoDB", "Express"], "ats_score": 88, "screening_score": 84, "final_score": 86, "ai_recommendation": "Backend Node Developer.", "candidate_summary": "Full stack JavaScript & Node backend specialist."},
            {"name": "Karthik Iyer", "email": "karthik.iyer@example.com", "phone": "+91 98765 43223", "status": "Interview", "experience": 6, "education": "B.Tech Electronics", "skills": ["C++", "Python", "Embedded Systems", "Linux"], "ats_score": 86, "screening_score": 82, "final_score": 84, "ai_recommendation": "Systems Engineer candidate.", "candidate_summary": "Systems developer working with low-level performance code."},
            {"name": "Pooja Hegde", "email": "pooja.hegde@example.com", "phone": "+91 98765 43224", "status": "Interview", "experience": 3, "education": "B.Tech Computer Science", "skills": ["Vue.js", "JavaScript", "CSS3", "HTML5"], "ats_score": 85, "screening_score": 81, "final_score": 83, "ai_recommendation": "UI Developer candidate.", "candidate_summary": "Frontend developer focused on web accessibility and design systems."},

            # Selected (3 total)
            {"name": "Amit Singh", "email": "amit.singh@example.com", "phone": "+91 98765 43225", "status": "Selected", "experience": 8, "education": "M.Tech Software Engineering", "skills": ["Python", "System Design", "AWS", "FastAPI", "Leadership"], "ats_score": 96, "screening_score": 94, "final_score": 95, "ai_recommendation": "Selected for Staff Software Engineer Offer.", "candidate_summary": "Top tier candidate with exceptional system design and team leadership skills."},
            {"name": "Ritu Agarwal", "email": "ritu.agarwal@example.com", "phone": "+91 98765 43226", "status": "Selected", "experience": 6, "education": "B.Tech Computer Science", "skills": ["React", "TypeScript", "Node.js", "GraphQL"], "ats_score": 95, "screening_score": 92, "final_score": 94, "ai_recommendation": "Selected for Principal Frontend Lead.", "candidate_summary": "Exceptional frontend lead engineer with product-driven mindset."},
            {"name": "Suresh Pillai", "email": "suresh.pillai@example.com", "phone": "+91 98765 43227", "status": "Selected", "experience": 9, "education": "Ph.D. Computer Science", "skills": ["Python", "PyTorch", "LLM", "Deep Learning", "Transformers"], "ats_score": 98, "screening_score": 96, "final_score": 97, "ai_recommendation": "Selected for Principal AI Scientist Offer.", "candidate_summary": "Renowned AI researcher with patents in NLP and transformer optimization."},

            # Shortlisted (12 total)
            *[{
                "name": f"Shortlisted Candidate {i}",
                "email": f"shortlist_{i}@example.com",
                "phone": f"+91 98765 {43228 + i}",
                "status": "Shortlisted",
                "experience": (i % 6) + 2,
                "education": ["B.Tech Computer Science", "M.Tech Data Science", "B.Sc IT"][i % 3],
                "skills": [["Python", "SQL"], ["React", "TypeScript"], ["FastAPI", "Docker"], ["AWS", "DevOps"]][i % 4],
                "ats_score": 88 + (i % 8),
                "screening_score": 83 + (i % 7),
                "final_score": 86 + (i % 7),
                "ai_recommendation": "Shortlisted for next round.",
                "candidate_summary": f"Qualified shortlisted professional with {(i % 6) + 2} years of domain experience."
            } for i in range(1, 13)],

            # Rejected (20 total)
            *[{
                "name": f"Applicant {i}",
                "email": f"rejected_{i}@example.com",
                "phone": f"+91 98765 {43240 + i}",
                "status": "Rejected",
                "experience": i % 3,
                "education": ["High School", "Diploma", "B.A. General"][i % 3],
                "skills": [["MS Office", "Excel"], ["Basic HTML"], ["Customer Support"]][i % 3],
                "ats_score": 40 + (i % 20),
                "screening_score": 38 + (i % 20),
                "final_score": 42 + (i % 20),
                "ai_recommendation": "Does not meet minimum technical skill and experience requirements.",
                "candidate_summary": "Candidate lacks required technical stack and core domain prerequisites."
            } for i in range(1, 21)]
        ]

        for cand_info in prompt_candidates:
            existing = db.query(Candidate).filter(Candidate.email == cand_info["email"]).first()
            if not existing:
                cand = Candidate(
                    name=cand_info["name"],
                    email=cand_info["email"],
                    phone=cand_info["phone"],
                    status=cand_info["status"],
                    experience=cand_info.get("experience", 2),
                    education=cand_info.get("education", "B.Tech Computer Science"),
                    skills=cand_info.get("skills", []),
                    projects=["Project Alpha", "Cloud Platform Initiative"],
                    notice_period="30 Days",
                    expected_ctc="15 LPA",
                    location="Mumbai / Hybrid",
                    ats_score=cand_info.get("ats_score", 85),
                    screening_score=cand_info.get("screening_score", 80),
                    final_score=cand_info.get("final_score", 82),
                    strengths=["Strong problem solving", "Solid core foundation", "Collaborative communicator"],
                    weaknesses=["Could gain deeper experience in enterprise Kubernetes clustering"],
                    ai_recommendation=cand_info.get("ai_recommendation", "Evaluated by AI Engine."),
                    candidate_summary=cand_info.get("candidate_summary", "Candidate profile evaluated."),
                    screening_responses=[
                        {"question": "What is your primary programming stack?", "response": "Python, FastAPI, and PostgreSQL.", "score": 90},
                        {"question": "How do you approach code quality & unit tests?", "response": "Strict TDD using pytest and automated CI/CD integration.", "score": 88}
                    ],
                    feedback="Preliminary recruiter screening notes: Candidate demonstrated strong problem solving capabilities."
                )
                db.add(cand)
        db.commit()
        logger.info("Successfully seeded 50 candidates.")
    except Exception as e:
        logger.error(f"Seeding candidates failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed test users & candidates
    logger.info("Application starting up... Initializing database tables.")
    Base.metadata.create_all(bind=engine)
    seed_users()
    seed_candidates()
    logger.info("Database tables initialized and seeded successfully.")
    yield
    # Shutdown: Clean up if needed
    logger.info("Application shutting down...")

app = FastAPI(
    title="RecruiterAI API",
    description="Backend API for candidate resumes and jobs screening",
    version="1.0.0",
    lifespan=lifespan
)

# Custom HTTP Middleware for detailed request logging and error handling
@app.middleware("http")
async def log_requests_and_handle_errors(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Incoming request: {request.method} {request.url.path} from {client_host}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Completed request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Completed in {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path} - "
            f"Error: {str(e)} - Elapsed time: {process_time:.2f}ms", 
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred on the server."}
        )

# Register routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(interviews.router)
app.include_router(communication.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "RecruiterAI API"}
