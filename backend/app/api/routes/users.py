from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import get_settings
from app.models import (
    Application,
    CandidateProfile,
    CandidateSkill,
    JobPost,
    Resume,
    Skill,
    User,
)
from app.schemas import CandidateProfileDetailPublic, CandidateProfilePublic, CandidateProfileUpdate
from app.services.audit_service import audit_service
from app.services.background_jobs import process_resume_analysis
from app.services.media_service import media_service

router = APIRouter(tags=["Users"])
settings = get_settings()


def _candidate_detail_query(db: Session):
    return db.query(CandidateProfile).options(
        joinedload(CandidateProfile.user),
        joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
        joinedload(CandidateProfile.educations),
        joinedload(CandidateProfile.experiences),
        joinedload(CandidateProfile.certifications),
        joinedload(CandidateProfile.languages),
        joinedload(CandidateProfile.resumes),
    )


@router.get("/users/profile", response_model=CandidateProfilePublic)
def get_my_profile(
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfile)
        .options(joinedload(CandidateProfile.user))
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return profile


@router.put("/users/profile", response_model=CandidateProfilePublic)
def update_my_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfile)
        .options(joinedload(CandidateProfile.user))
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    audit_service.log(
        db,
        user_id=current_user.id,
        action="candidate.profile.update",
        entity_type="candidate_profile",
        entity_id=str(profile.id),
    )
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/users/profile/avatar", response_model=CandidateProfilePublic)
def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfile)
        .options(joinedload(CandidateProfile.user))
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    media_service.delete_uploaded_file(profile.avatar_url, settings.upload_dir)
    profile.avatar_url = media_service.save_image(file, settings.upload_dir, "avatars")
    audit_service.log(
        db,
        user_id=current_user.id,
        action="candidate.profile.avatar.upload",
        entity_type="candidate_profile",
        entity_id=str(profile.id),
    )
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/candidates/{candidate_id}", response_model=CandidateProfileDetailPublic)
def get_candidate(
    candidate_id: int,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    profile = _candidate_detail_query(db).filter(CandidateProfile.id == candidate_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.name == "company":
        allowed = (
            db.query(Application)
            .join(JobPost, JobPost.id == Application.job_id)
            .filter(
                Application.candidate_id == profile.id,
                JobPost.company_id == current_user.company_id,
            )
            .first()
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Cannot access this candidate")
    if profile.resumes and not (profile.educations or profile.experiences or profile.languages):
        latest_resume = sorted(profile.resumes, key=lambda item: item.version, reverse=True)[0]
        process_resume_analysis(latest_resume.id)
        db.expire_all()
        profile = _candidate_detail_query(db).filter(CandidateProfile.id == candidate_id).first()
    return profile
