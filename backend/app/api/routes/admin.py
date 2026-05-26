from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models import (
    Application,
    AuditLog,
    CandidateProfile,
    Company,
    JobCategory,
    JobPost,
    Message,
    Notification,
    Skill,
    User,
)
from app.schemas import (
    AdminActionResponse,
    CompanyPublic,
    JobCategoryCreate,
    JobCategoryPublic,
    SkillCreate,
    SkillPublic,
    SystemOverview,
    UserPublic,
)
from app.services.audit_service import audit_service
from app.services.cache_service import cache_service

router = APIRouter(prefix="/admin", tags=["Admin"])