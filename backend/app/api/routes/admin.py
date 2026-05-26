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