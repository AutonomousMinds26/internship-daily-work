import os
import time
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth import RoleChecker, get_password_hash, User as AuthUser
from app.config import settings
from app.models import User, IntegrationConfig, AuditLog, Candidate, Job, Offer
from app.schemas import (
    UserAdminCreate, UserRoleUpdate, UserAdminResponse,
    IntegrationConfigCreate, IntegrationConfigResponse,
    AuditLogResponse
)

router = APIRouter(prefix="/admin", tags=["admin"])

admin_checker = RoleChecker(allowed_roles=["Admin"])


@router.get("/users", response_model=List[UserAdminResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(admin_checker)
):
    """
    List all platform users with roles and activity timestamps (Admin only).
    """
    return db.query(User).offset(skip).limit(limit).all()


@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    user_in: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(admin_checker)
):
    """
    Create a new user with explicit role and team assignment (Admin only).
    """
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered.")

    new_user = User(
        username=user_in.username,
        email=str(user_in.email) if user_in.email else None,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        organization_id=user_in.organization_id,
        hiring_team_id=user_in.hiring_team_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="USER_CREATE",
        resource_type="User",
        resource_id=str(new_user.id),
        details={"created_user": new_user.username, "role": new_user.role}
    )
    db.add(audit)
    db.commit()

    return new_user


@router.put("/users/{id}/role", response_model=UserAdminResponse)
def update_user_role(
    id: int,
    update_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(admin_checker)
):
    """
    Update a user's role or active status (Admin only).
    """
    user_rec = db.query(User).filter(User.id == id).first()
    if not user_rec:
        raise HTTPException(status_code=404, detail="User not found.")

    old_role = user_rec.role
    user_rec.role = update_in.role
    if update_in.is_active is not None:
        user_rec.is_active = update_in.is_active
    if update_in.hiring_team_id is not None:
        user_rec.hiring_team_id = update_in.hiring_team_id

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ROLE_UPDATE",
        resource_type="User",
        resource_id=str(id),
        details={"target_user": user_rec.username, "old_role": old_role, "new_role": user_rec.role}
    )
    db.add(audit)
    db.commit()
    db.refresh(user_rec)

    return user_rec


@router.get("/integrations", response_model=List[IntegrationConfigResponse])
def list_integrations(
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(admin_checker)
):
    """
    List configured external integrations and their synchronization status.
    """
    default_providers = [
        ("GoogleCalendar", "Calendar"),
        ("OutlookCalendar", "Calendar"),
        ("HackerRank", "Assessment"),
        ("Codility", "Assessment"),
        ("MercerMettl", "Assessment"),
        ("SendGrid", "Email"),
        ("Checkr", "BackgroundCheck"),
        ("SpringVerify", "BackgroundCheck"),
        ("Greenhouse", "ATS"),
        ("Lever", "ATS"),
    ]

    for name, cat in default_providers:
        existing = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == name).first()
        if not existing:
            cfg = IntegrationConfig(
                provider_name=name,
                provider_category=cat,
                is_enabled=True,
                config_data={"status": "active_mock" if settings.USE_MOCK_APIS else "live"}
            )
            db.add(cfg)
    db.commit()

    return db.query(IntegrationConfig).all()


@router.post("/integrations", response_model=IntegrationConfigResponse)
def configure_integration(
    cfg_in: IntegrationConfigCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(admin_checker)
):
    """
    Enable, disable, or configure an external integration provider.
    """
    cfg = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == cfg_in.provider_name).first()
    if not cfg:
        cfg = IntegrationConfig(
            provider_name=cfg_in.provider_name,
            provider_category=cfg_in.provider_category,
            is_enabled=cfg_in.is_enabled,
            config_data=cfg_in.config_data or {}
        )
        db.add(cfg)
    else:
        cfg.is_enabled = cfg_in.is_enabled
        if cfg_in.config_data:
            cfg.config_data = cfg_in.config_data
        cfg.last_sync_at = datetime.now(timezone.utc)

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="INTEGRATION_CONFIG",
        resource_type="Integration",
        resource_id=cfg_in.provider_name,
        details={"provider": cfg_in.provider_name, "is_enabled": cfg_in.is_enabled}
    )
    db.add(audit)
    db.commit()
    db.refresh(cfg)

    return cfg


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(admin_checker)
):
    """
    Query platform security and activity audit logs with filters.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if username:
        query = query.filter(AuditLog.username == username)

    return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()


@router.get("/system-status")
def get_system_status(
    db: Session = Depends(get_db),
    _current_user: AuthUser = Depends(admin_checker)
):
    """
    Return comprehensive platform health, Celery/Redis status, and database statistics.
    """
    # Check DB
    db_ok = True
    try:
        user_count = db.query(User).count()
        cand_count = db.query(Candidate).count()
        job_count = db.query(Job).count()
        offer_count = db.query(Offer).count()
    except Exception:
        db_ok = False
        user_count = cand_count = job_count = offer_count = 0

    # Check Celery/Redis
    redis_ok = False
    try:
        from app.tasks.celery_app import celery_app
        insp = celery_app.control.inspect()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "Healthy" if db_ok else "Degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": "Connected" if db_ok else "Error",
            "type": "SQLite" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL",
            "counts": {
                "users": user_count,
                "candidates": cand_count,
                "jobs": job_count,
                "offers": offer_count
            }
        },
        "background_worker": {
            "broker": "Redis",
            "broker_url_configured": bool(settings.CELERY_BROKER_URL),
            "status": "Online (Redis Mode)" if redis_ok else "Sandbox Eager Mode"
        },
        "llm_provider": {
            "active_provider": settings.LLM_PROVIDER,
            "has_groq_key": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "gsk_placeholder_key"),
            "has_openai_key": bool(settings.OPENAI_API_KEY),
            "has_anthropic_key": bool(settings.ANTHROPIC_API_KEY)
        },
        "integrations_mode": "Mock/Sandbox" if settings.USE_MOCK_APIS else "Live External Credentials"
    }
