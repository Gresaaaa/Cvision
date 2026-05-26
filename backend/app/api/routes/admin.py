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
@router.get("/users", response_model=list[UserPublic])
def list_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .order_by(User.created_at.desc())
        .all()
    )


@router.get("/companies", response_model=list[CompanyPublic])
def list_companies(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.created_at.desc()).all()


def _delete_user_record(db: Session, user: User) -> None:
    if user.owned_company:
        user.owned_company.owner_user_id = None

    db.query(AuditLog).filter(AuditLog.user_id == user.id).update(
        {AuditLog.user_id: None},
        synchronize_session=False,
    )
    db.query(Message).filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    ).delete(synchronize_session=False)
    db.delete(user)


@router.patch("/users/{user_id}/deactivate", response_model=AdminActionResponse)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")
    if not user.is_active:
        return AdminActionResponse(message=f"{user.email} is already inactive.")

    user.is_active = False
    audit_service.log(
        db,
        user_id=current_user.id,
        action="admin.user.deactivate",
        entity_type="user",
        entity_id=str(user.id),
        company_id=user.company_id,
        details={"email": user.email},
    )
    db.commit()
    return AdminActionResponse(message=f"{user.email} was deactivated.")


@router.patch("/users/{user_id}/reactivate", response_model=AdminActionResponse)
def reactivate_user(
    user_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active:
        return AdminActionResponse(message=f"{user.email} is already active.")

    user.is_active = True
    audit_service.log(
        db,
        user_id=current_user.id,
        action="admin.user.reactivate",
        entity_type="user",
        entity_id=str(user.id),
        company_id=user.company_id,
        details={"email": user.email},
    )
    db.commit()
    return AdminActionResponse(message=f"{user.email} was reactivated.")
