from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models import User
from app.auth import verify_password, create_access_token, get_password_hash
from app.schemas import Token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# ── Schemas ───────────────────────────────────────────────────────────────────

ALLOWED_ROLES = {"Recruiter", "Hiring Manager", "Admin", "Candidate"}

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="Candidate", description="One of: Recruiter, Hiring Manager, Admin, Candidate")
    full_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)

class RegisterResponse(BaseModel):
    message: str
    username: str
    role: str
    access_token: str
    token_type: str = "bearer"

# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, str(user.password_hash)):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Successful login for user '{user.username}' (role: {user.role})")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and return a JWT for immediate login."""

    # Validate role
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{payload.role}'. Must be one of: {', '.join(sorted(ALLOWED_ROLES))}"
        )

    # Check username uniqueness
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken. Please choose another."
        )

    # Create user
    new_user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: '{payload.username}' (role: {payload.role})")

    # Auto-login: return JWT so frontend can skip the login step
    access_token = create_access_token(data={"sub": new_user.username, "role": new_user.role})
    return RegisterResponse(
        message=f"Account created successfully! Welcome to RecruiterAI, {payload.username}.",
        username=new_user.username,
        role=new_user.role,
        access_token=access_token,
        token_type="bearer"
    )

from app.auth import oauth2_scheme

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(token: str = Depends(oauth2_scheme)):
    """
    Log out user by blacklisting current JWT token.
    """
    try:
        from jose import jwt
        from app.config import settings
        import time
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            ttl = int(exp - time.time())
            if ttl > 0:
                from app.services.redis_cache import blacklist_token
                blacklist_token(token, ttl)
    except Exception as e:
        logger.error(f"Error blacklisting token on logout: {str(e)}")
        from app.services.redis_cache import blacklist_token
        blacklist_token(token, 3600)
    return {"detail": "Successfully logged out"}
