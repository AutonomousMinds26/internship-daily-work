import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.auth import get_password_hash
from app.models import User, Candidate, Job
import app.services.redis_cache as redis_cache

# Mock Redis class
class MockRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return 1
        return 0

# Set up in-memory SQLite database for testing with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a clean database session for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed default users
    users = [
        ("admin_user", "Admin"),
        ("recruiter_user", "Recruiter"),
        ("manager_user", "Hiring Manager")
    ]
    for username, role in users:
        password_hash = get_password_hash("password123")
        user = User(
            username=username,
            password_hash=password_hash,
            role=role
        )
        session.add(user)
    session.commit()

    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a FastAPI TestClient that overrides the get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
def mock_redis():
    """Automatically mock the Redis client for all tests."""
    original_client = redis_cache.redis_client
    mocked = MockRedis()
    redis_cache.redis_client = mocked
    yield mocked
    redis_cache.redis_client = original_client
