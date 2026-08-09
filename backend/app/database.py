from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings


# Determine if we're using SQLite or another DB (e.g. PostgreSQL)
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_db_migrations():
    import sqlite3
    import logging
    logger = logging.getLogger(__name__)
    
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    
    db_path = settings.DATABASE_URL.replace("sqlite:///./", "").replace("sqlite:///", "")
    logger.info(f"Running SQLite migrations on {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        def column_exists(table_name, col_name):
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [info[1] for info in cursor.fetchall()]
                return col_name in columns
            except Exception:
                return False

        # 1. Candidates table
        if not column_exists("candidates", "status"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN status VARCHAR DEFAULT 'Applied'")
            logger.info("Migration: Added column 'status' to 'candidates'")
        if not column_exists("candidates", "ai_summary"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN ai_summary TEXT")
            logger.info("Migration: Added column 'ai_summary' to 'candidates'")
        if not column_exists("candidates", "resume_hash"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN resume_hash VARCHAR")
            logger.info("Migration: Added column 'resume_hash' to 'candidates'")
        if not column_exists("candidates", "ats_score"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN ats_score FLOAT DEFAULT 0.0")
            logger.info("Migration: Added column 'ats_score' to 'candidates'")
        if not column_exists("candidates", "match_score"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN match_score FLOAT DEFAULT 0.0")
            logger.info("Migration: Added column 'match_score' to 'candidates'")
        if not column_exists("candidates", "screening_score"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN screening_score FLOAT DEFAULT 0.0")
            logger.info("Migration: Added column 'screening_score' to 'candidates'")
        if not column_exists("candidates", "final_score"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN final_score FLOAT DEFAULT 0.0")
            logger.info("Migration: Added column 'final_score' to 'candidates'")
        if not column_exists("candidates", "ats_details"):
            cursor.execute("ALTER TABLE candidates ADD COLUMN ats_details JSON")
            logger.info("Migration: Added column 'ats_details' to 'candidates'")

            
        # 2. Resumes table
        if not column_exists("resumes", "embedding"):
            cursor.execute("ALTER TABLE resumes ADD COLUMN embedding JSON")
            logger.info("Migration: Added column 'embedding' to 'resumes'")

        # 3. Candidate_scores table
        if not column_exists("candidate_scores", "skill_gap_report"):
            cursor.execute("ALTER TABLE candidate_scores ADD COLUMN skill_gap_report JSON")
            logger.info("Migration: Added column 'skill_gap_report' to 'candidate_scores'")

        # 4. Interviews table
        if not column_exists("interviews", "calendar_event_id"):
            cursor.execute("ALTER TABLE interviews ADD COLUMN calendar_event_id VARCHAR")
            logger.info("Migration: Added column 'calendar_event_id' to 'interviews'")
        if not column_exists("interviews", "calendar_invite"):
            cursor.execute("ALTER TABLE interviews ADD COLUMN calendar_invite TEXT")
            logger.info("Migration: Added column 'calendar_invite' to 'interviews'")

        conn.commit()
        conn.close()
        logger.info("SQLite migrations completed successfully.")
    except Exception as e:
        logger.error(f"Failed to execute SQLite migrations: {str(e)}")

