import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal, run_db_migrations
from app.logging_config import setup_logging
import random
from app.models import User, Candidate
from app.auth import get_password_hash
from app.routes import (
    auth, jobs, candidates, interviews, emails, monitoring, ai, tools,
    extended_api, admin, offers, privacy, websockets
)

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
            ("alice.smith@example.com", "Candidate"),
            ("candidate_user", "Candidate"),
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
        logger.error(f"Seeding failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

def seed_candidates():
    """Seed 50 demo candidates with realistic data for the A2 Recruiter Dashboard."""
    db = SessionLocal()
    try:
        existing_count = db.query(Candidate).count()
        if existing_count >= 50:
            return

        random.seed(42)
        candidate_data = [
            # Applied (7 candidates)
            {"name": "Rahul Sharma", "email": "rahul.sharma@example.com", "phone": "9876543210", "education": "B.Tech Computer Science", "experience": 2, "skills": ["Python", "Django", "SQL"], "location": "Mumbai", "status": "Applied", "ats_score": 72.0, "match_score": 68.0, "screening_score": 70.0, "final_score": 70.0},
            {"name": "Rohan Verma", "email": "rohan.verma@example.com", "phone": "9876543211", "education": "B.E. Electronics", "experience": 1, "skills": ["Java", "Spring Boot"], "location": "Pune", "status": "Applied", "ats_score": 65.0, "match_score": 60.0, "screening_score": 62.0, "final_score": 62.0},
            {"name": "Kavya Nair", "email": "kavya.nair@example.com", "phone": "9876543220", "education": "MCA", "experience": 1, "skills": ["React", "JavaScript"], "location": "Kochi", "status": "Applied", "ats_score": 68.0, "match_score": 65.0, "screening_score": 66.0, "final_score": 66.0},
            {"name": "Nikhil Joshi", "email": "nikhil.joshi@example.com", "phone": "9876543221", "education": "B.Sc IT", "experience": 0, "skills": ["HTML", "CSS", "JavaScript"], "location": "Nagpur", "status": "Applied", "ats_score": 55.0, "match_score": 52.0, "screening_score": 53.0, "final_score": 53.0},
            {"name": "Pooja Singh", "email": "pooja.singh@example.com", "phone": "9876543222", "education": "B.Tech IT", "experience": 2, "skills": ["Node.js", "MongoDB", "Express"], "location": "Delhi", "status": "Applied", "ats_score": 74.0, "match_score": 70.0, "screening_score": 72.0, "final_score": 72.0},
            {"name": "Arjun Patel", "email": "arjun.patel@example.com", "phone": "9876543223", "education": "B.E. CSE", "experience": 1, "skills": ["C++", "Algorithms"], "location": "Ahmedabad", "status": "Applied", "ats_score": 60.0, "match_score": 58.0, "screening_score": 59.0, "final_score": 59.0},
            {"name": "Tanvi Desai", "email": "tanvi.desai@example.com", "phone": "9876543224", "education": "M.Tech CSE", "experience": 3, "skills": ["Data Science", "ML", "Python"], "location": "Surat", "status": "Applied", "ats_score": 78.0, "match_score": 75.0, "screening_score": 76.0, "final_score": 76.0},
            # Screening (3 candidates)
            {"name": "Vivek Reddy", "email": "vivek.reddy@example.com", "phone": "9876543212", "education": "B.Tech CSE", "experience": 2, "skills": ["SQL", "Python", "Tableau"], "location": "Hyderabad", "status": "Screening", "ats_score": 75.0, "match_score": 72.0, "screening_score": 73.0, "final_score": 73.0},
            {"name": "Meera Krishnan", "email": "meera.krishnan@example.com", "phone": "9876543225", "education": "M.Sc Statistics", "experience": 2, "skills": ["R", "Python", "Statistics"], "location": "Chennai", "status": "Screening", "ats_score": 76.0, "match_score": 73.0, "screening_score": 74.0, "final_score": 74.0},
            {"name": "Siddharth Roy", "email": "siddharth.roy@example.com", "phone": "9876543226", "education": "B.Tech ECE", "experience": 1, "skills": ["IoT", "Embedded C"], "location": "Kolkata", "status": "Screening", "ats_score": 66.0, "match_score": 63.0, "screening_score": 64.0, "final_score": 64.0},
            # Shortlisted (12 candidates)
            {"name": "Ananya Iyer", "email": "ananya.iyer@example.com", "phone": "9876543213", "education": "M.Tech AI", "experience": 3, "skills": ["Machine Learning", "TensorFlow", "Python"], "location": "Bangalore", "status": "Shortlisted", "ats_score": 88.0, "match_score": 85.0, "screening_score": 86.0, "final_score": 86.0},
            {"name": "Sneha Kulkarni", "email": "sneha.kulkarni@example.com", "phone": "9876543214", "education": "B.Tech CSE", "experience": 4, "skills": ["React", "Node.js", "MongoDB"], "location": "Pune", "status": "Shortlisted", "ats_score": 85.0, "match_score": 82.0, "screening_score": 83.0, "final_score": 83.0},
            {"name": "Karan Mehta", "email": "karan.mehta@example.com", "phone": "9876543227", "education": "B.E. IT", "experience": 3, "skills": ["AWS", "DevOps", "Docker"], "location": "Mumbai", "status": "Shortlisted", "ats_score": 82.0, "match_score": 80.0, "screening_score": 81.0, "final_score": 81.0},
            {"name": "Richa Gupta", "email": "richa.gupta@example.com", "phone": "9876543228", "education": "MCA", "experience": 2, "skills": ["Java", "Spring", "Hibernate"], "location": "Delhi", "status": "Shortlisted", "ats_score": 80.0, "match_score": 77.0, "screening_score": 78.0, "final_score": 78.0},
            {"name": "Dhruv Malhotra", "email": "dhruv.malhotra@example.com", "phone": "9876543229", "education": "B.Tech CSE", "experience": 5, "skills": ["Python", "Django", "PostgreSQL", "Redis"], "location": "Hyderabad", "status": "Shortlisted", "ats_score": 90.0, "match_score": 88.0, "screening_score": 89.0, "final_score": 89.0},
            {"name": "Ishita Banerjee", "email": "ishita.banerjee@example.com", "phone": "9876543230", "education": "M.Tech Data Science", "experience": 3, "skills": ["PyTorch", "NLP", "Python"], "location": "Bangalore", "status": "Shortlisted", "ats_score": 87.0, "match_score": 84.0, "screening_score": 85.0, "final_score": 85.0},
            {"name": "Ravi Shankar", "email": "ravi.shankar@example.com", "phone": "9876543231", "education": "B.E. CSE", "experience": 4, "skills": ["Kubernetes", "CI/CD", "Linux"], "location": "Chennai", "status": "Shortlisted", "ats_score": 83.0, "match_score": 81.0, "screening_score": 82.0, "final_score": 82.0},
            {"name": "Sonam Tiwari", "email": "sonam.tiwari@example.com", "phone": "9876543232", "education": "B.Tech IT", "experience": 2, "skills": ["Vue.js", "JavaScript", "CSS"], "location": "Jaipur", "status": "Shortlisted", "ats_score": 79.0, "match_score": 76.0, "screening_score": 77.0, "final_score": 77.0},
            {"name": "Aditya Kumar", "email": "aditya.kumar@example.com", "phone": "9876543233", "education": "B.Sc Computer Science", "experience": 3, "skills": ["Angular", "TypeScript", "RxJS"], "location": "Noida", "status": "Shortlisted", "ats_score": 81.0, "match_score": 79.0, "screening_score": 80.0, "final_score": 80.0},
            {"name": "Prerna Jain", "email": "prerna.jain@example.com", "phone": "9876543234", "education": "M.E. Software Engineering", "experience": 4, "skills": ["Microservices", "Java", "Kafka"], "location": "Pune", "status": "Shortlisted", "ats_score": 86.0, "match_score": 83.0, "screening_score": 84.0, "final_score": 84.0},
            {"name": "Manish Rao", "email": "manish.rao@example.com", "phone": "9876543235", "education": "B.Tech CSE", "experience": 2, "skills": ["Flutter", "Dart", "Firebase"], "location": "Bangalore", "status": "Shortlisted", "ats_score": 77.0, "match_score": 75.0, "screening_score": 76.0, "final_score": 76.0},
            {"name": "Swati Pandey", "email": "swati.pandey@example.com", "phone": "9876543236", "education": "MCA", "experience": 3, "skills": ["Selenium", "QA", "Python"], "location": "Lucknow", "status": "Shortlisted", "ats_score": 78.0, "match_score": 76.0, "screening_score": 77.0, "final_score": 77.0},
            # Interview (8 candidates)
            {"name": "Priya Menon", "email": "priya.menon@example.com", "phone": "9876543215", "education": "B.Tech CSE", "experience": 5, "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"], "location": "Bangalore", "status": "Interview Scheduled", "ats_score": 91.0, "match_score": 87.0, "screening_score": 84.0, "final_score": 88.0},
            {"name": "Gaurav Mishra", "email": "gaurav.mishra@example.com", "phone": "9876543237", "education": "M.Tech CSE", "experience": 4, "skills": ["ML", "Deep Learning", "Python"], "location": "Delhi", "status": "Interview Scheduled", "ats_score": 89.0, "match_score": 86.0, "screening_score": 87.0, "final_score": 87.0},
            {"name": "Nisha Agarwal", "email": "nisha.agarwal@example.com", "phone": "9876543238", "education": "B.E. CSE", "experience": 3, "skills": ["Full Stack", "React", "Node.js"], "location": "Mumbai", "status": "Interview Scheduled", "ats_score": 86.0, "match_score": 83.0, "screening_score": 84.0, "final_score": 84.0},
            {"name": "Rajesh Pillai", "email": "rajesh.pillai@example.com", "phone": "9876543239", "education": "B.Tech IT", "experience": 6, "skills": ["Java", "Microservices", "AWS", "Kubernetes"], "location": "Hyderabad", "status": "Interview Scheduled", "ats_score": 92.0, "match_score": 89.0, "screening_score": 90.0, "final_score": 90.0},
            {"name": "Shruti Kapoor", "email": "shruti.kapoor@example.com", "phone": "9876543240", "education": "MCA", "experience": 4, "skills": ["Android", "Kotlin", "Java"], "location": "Noida", "status": "Interview Scheduled", "ats_score": 84.0, "match_score": 81.0, "screening_score": 82.0, "final_score": 82.0},
            {"name": "Varun Saxena", "email": "varun.saxena@example.com", "phone": "9876543241", "education": "B.Tech CSE", "experience": 5, "skills": ["Cloud", "GCP", "Terraform"], "location": "Bangalore", "status": "Interview Scheduled", "ats_score": 88.0, "match_score": 85.0, "screening_score": 86.0, "final_score": 86.0},
            {"name": "Anjali Srivastava", "email": "anjali.srivastava@example.com", "phone": "9876543242", "education": "M.Tech AI", "experience": 3, "skills": ["NLP", "BERT", "Python"], "location": "Chennai", "status": "Interview Scheduled", "ats_score": 87.0, "match_score": 84.0, "screening_score": 85.0, "final_score": 85.0},
            {"name": "Mohit Choudhary", "email": "mohit.choudhary@example.com", "phone": "9876543243", "education": "B.E. IT", "experience": 4, "skills": ["DevSecOps", "Docker", "Python"], "location": "Jaipur", "status": "Interview Scheduled", "ats_score": 85.0, "match_score": 82.0, "screening_score": 83.0, "final_score": 83.0},
            # Selected (3 candidates)
            {"name": "Amit Bose", "email": "amit.bose@example.com", "phone": "9876543216", "education": "M.Tech CSE", "experience": 7, "skills": ["Python", "ML", "Data Science", "SQL", "TensorFlow"], "location": "Bangalore", "status": "Selected", "ats_score": 95.0, "match_score": 92.0, "screening_score": 93.0, "final_score": 93.0},
            {"name": "Deepika Nanda", "email": "deepika.nanda@example.com", "phone": "9876543244", "education": "B.Tech CSE", "experience": 6, "skills": ["Full Stack", "React", "Python", "AWS"], "location": "Hyderabad", "status": "Selected", "ats_score": 93.0, "match_score": 91.0, "screening_score": 92.0, "final_score": 92.0},
            {"name": "Suresh Natarajan", "email": "suresh.natarajan@example.com", "phone": "9876543245", "education": "M.E. Software Engineering", "experience": 8, "skills": ["Architecture", "Java", "Microservices", "Kafka", "Redis"], "location": "Chennai", "status": "Selected", "ats_score": 96.0, "match_score": 94.0, "screening_score": 95.0, "final_score": 95.0},
            # Rejected (20 candidates)
            {"name": "Ramesh Babu", "email": "ramesh.babu@example.com", "phone": "9876543217", "education": "B.Sc", "experience": 0, "skills": ["MS Office"], "location": "Vizag", "status": "Rejected", "ats_score": 32.0, "match_score": 28.0, "screening_score": 30.0, "final_score": 30.0},
            {"name": "Geeta Sharma", "email": "geeta.sharma@example.com", "phone": "9876543218", "education": "BA English", "experience": 0, "skills": ["Communication"], "location": "Bhopal", "status": "Rejected", "ats_score": 25.0, "match_score": 22.0, "screening_score": 23.0, "final_score": 23.0},
            {"name": "Sunil Yadav", "email": "sunil.yadav@example.com", "phone": "9876543219", "education": "B.Com", "experience": 1, "skills": ["Tally", "Accounting"], "location": "Indore", "status": "Rejected", "ats_score": 28.0, "match_score": 25.0, "screening_score": 26.0, "final_score": 26.0},
            {"name": "Lalitha Subramaniam", "email": "lalitha.subramaniam@example.com", "phone": "9876543246", "education": "B.Sc Maths", "experience": 0, "skills": ["Excel"], "location": "Coimbatore", "status": "Rejected", "ats_score": 20.0, "match_score": 18.0, "screening_score": 19.0, "final_score": 19.0},
            {"name": "Prakash Tiwari", "email": "prakash.tiwari@example.com", "phone": "9876543247", "education": "B.E. Mechanical", "experience": 2, "skills": ["AutoCAD"], "location": "Kanpur", "status": "Rejected", "ats_score": 35.0, "match_score": 30.0, "screening_score": 32.0, "final_score": 32.0},
            {"name": "Rekha Sinha", "email": "rekha.sinha@example.com", "phone": "9876543248", "education": "M.A. Economics", "experience": 0, "skills": ["Research"], "location": "Patna", "status": "Rejected", "ats_score": 22.0, "match_score": 19.0, "screening_score": 20.0, "final_score": 20.0},
            {"name": "Mohan Das", "email": "mohan.das@example.com", "phone": "9876543249", "education": "B.Tech Civil", "experience": 1, "skills": ["AutoCAD", "Revit"], "location": "Bhubaneswar", "status": "Rejected", "ats_score": 30.0, "match_score": 27.0, "screening_score": 28.0, "final_score": 28.0},
            {"name": "Kavitha Rajan", "email": "kavitha.rajan@example.com", "phone": "9876543250", "education": "MBA HR", "experience": 3, "skills": ["HR", "Recruitment"], "location": "Bangalore", "status": "Rejected", "ats_score": 40.0, "match_score": 35.0, "screening_score": 37.0, "final_score": 37.0},
            {"name": "Sanjay Kumar", "email": "sanjay.kumar@example.com", "phone": "9876543251", "education": "B.Tech EEE", "experience": 2, "skills": ["MATLAB", "Electrical"], "location": "Coimbatore", "status": "Rejected", "ats_score": 33.0, "match_score": 29.0, "screening_score": 31.0, "final_score": 31.0},
            {"name": "Asha Reddy", "email": "asha.reddy@example.com", "phone": "9876543252", "education": "B.Sc Chemistry", "experience": 0, "skills": ["Lab Research"], "location": "Hyderabad", "status": "Rejected", "ats_score": 18.0, "match_score": 15.0, "screening_score": 16.0, "final_score": 16.0},
            {"name": "Vijay Anand", "email": "vijay.anand@example.com", "phone": "9876543253", "education": "B.Tech Mechanical", "experience": 3, "skills": ["SolidWorks", "Manufacturing"], "location": "Pune", "status": "Rejected", "ats_score": 38.0, "match_score": 34.0, "screening_score": 36.0, "final_score": 36.0},
            {"name": "Poonam Chauhan", "email": "poonam.chauhan@example.com", "phone": "9876543254", "education": "B.Sc Physics", "experience": 0, "skills": ["Teaching"], "location": "Jaipur", "status": "Rejected", "ats_score": 21.0, "match_score": 17.0, "screening_score": 19.0, "final_score": 19.0},
            {"name": "Arun Pillai", "email": "arun.pillai@example.com", "phone": "9876543255", "education": "Diploma Engineering", "experience": 1, "skills": ["Welding", "Fitting"], "location": "Kochi", "status": "Rejected", "ats_score": 27.0, "match_score": 23.0, "screening_score": 25.0, "final_score": 25.0},
            {"name": "Nandini Saxena", "email": "nandini.saxena@example.com", "phone": "9876543256", "education": "M.A. History", "experience": 0, "skills": ["Writing"], "location": "Agra", "status": "Rejected", "ats_score": 15.0, "match_score": 12.0, "screening_score": 13.0, "final_score": 13.0},
            {"name": "Balu Krishnamurthy", "email": "balu.krishnamurthy@example.com", "phone": "9876543257", "education": "B.Tech CSE", "experience": 0, "skills": ["C", "C++"], "location": "Coimbatore", "status": "Rejected", "ats_score": 45.0, "match_score": 40.0, "screening_score": 42.0, "final_score": 42.0},
            {"name": "Mala Srivastav", "email": "mala.srivastav@example.com", "phone": "9876543258", "education": "B.Com", "experience": 2, "skills": ["Finance", "GST"], "location": "Lucknow", "status": "Rejected", "ats_score": 29.0, "match_score": 24.0, "screening_score": 26.0, "final_score": 26.0},
            {"name": "Harish Gowda", "email": "harish.gowda@example.com", "phone": "9876543259", "education": "Diploma CSE", "experience": 1, "skills": ["PHP", "MySQL"], "location": "Mysuru", "status": "Rejected", "ats_score": 42.0, "match_score": 38.0, "screening_score": 40.0, "final_score": 40.0},
            {"name": "Shilpa Verma", "email": "shilpa.verma@example.com", "phone": "9876543260", "education": "BCA", "experience": 0, "skills": ["VB.NET", "MS Access"], "location": "Gwalior", "status": "Rejected", "ats_score": 31.0, "match_score": 27.0, "screening_score": 29.0, "final_score": 29.0},
            {"name": "Rajiv Mathew", "email": "rajiv.mathew@example.com", "phone": "9876543261", "education": "B.Tech IT", "experience": 1, "skills": ["Basic Python"], "location": "Thiruvananthapuram", "status": "Rejected", "ats_score": 48.0, "match_score": 44.0, "screening_score": 46.0, "final_score": 46.0},
            {"name": "Divya Prabhu", "email": "divya.prabhu@example.com", "phone": "9876543262", "education": "BBA", "experience": 0, "skills": ["Marketing", "Social Media"], "location": "Mangalore", "status": "Rejected", "ats_score": 17.0, "match_score": 13.0, "screening_score": 15.0, "final_score": 15.0},
        ]

        for data in candidate_data:
            existing = db.query(Candidate).filter(Candidate.email == data["email"]).first()
            if not existing:
                candidate = Candidate(**data)
                db.add(candidate)
        db.commit()
        logger.info(f"Seeded {len(candidate_data)} demo candidates for A2 Recruiter Dashboard.")
    except Exception as e:
        logger.error(f"Candidate seeding failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables, run migrations, and seed test users
    logger.info("Application starting up... Initializing database tables.")
    Base.metadata.create_all(bind=engine)
    try:
        run_db_migrations()
    except Exception as e:
        logger.error(f"Failed to run database migrations: {str(e)}")
    seed_users()
    seed_candidates()
    logger.info("Database tables initialized and seeded successfully.")
    yield

    # Shutdown: Clean up if needed
    logger.info("Application shutting down...")

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
import redis

app = FastAPI(
    title="RecruiterAI API",
    description="Enterprise Multi-tenant ATS & Autonomous AI Talent Acquisition Platform.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database connection exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection error. Please try again later."}
    )

@app.exception_handler(redis.exceptions.RedisError)
async def redis_exception_handler(request: Request, exc: redis.exceptions.RedisError):
    logger.error(f"Redis cache exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Cache service error. Please try again."}
    )

# Custom HTTP Middleware for detailed request logging and audit tracking
@app.middleware("http")
async def log_requests_and_handle_errors(request: Request, call_next):
    start_time = time.time()
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
app.include_router(emails.router)
app.include_router(monitoring.router)
app.include_router(ai.router)
app.include_router(tools.router)
app.include_router(extended_api.router)
app.include_router(admin.router)
app.include_router(offers.router)
app.include_router(privacy.router)
app.include_router(websockets.router)

@app.get("/")
def home():
    return {
        "status": "healthy",
        "service": "RecruiterAI Enterprise API",
        "version": "2.0.0",
        "track": "Track B Complete"
    }

