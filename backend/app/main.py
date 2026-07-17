import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.logging_config import setup_logging
from app.models import User
from app.auth import get_password_hash
from app.routes import auth, jobs, candidates

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
            ("manager_user", "Hiring Manager")
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed test users
    logger.info("Application starting up... Initializing database tables.")
    Base.metadata.create_all(bind=engine)
    seed_users()
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

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "RecruiterAI API"}
