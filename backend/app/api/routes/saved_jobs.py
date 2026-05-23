from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models import CandidateProfile, JobPost, SavedJob, User
from app.schemas import SavedJobPublic
from app.services.audit_service import audit_service

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])


@router.post("/{job_id}", response_model=SavedJobPublic)
def save_job(
    job_id: int,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    job = db.query(JobPost).filter(JobPost.id == job_id, JobPost.is_active.is_(True)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.query(SavedJob).filter(SavedJob.candidate_id == profile.id, SavedJob.job_id == job_id).first()
    if existing:
        return (
            db.query(SavedJob)
            .options(joinedload(SavedJob.job).joinedload(JobPost.company))
            .filter(SavedJob.id == existing.id)
            .first()
        )
    saved = SavedJob(candidate_id=profile.id, job_id=job_id)
    db.add(saved)
    db.flush()
    audit_service.log(
        db,
        user_id=current_user.id,
        action="job.save",
        entity_type="saved_job",
        entity_id=str(saved.id),
    )
    db.commit()
    return (
        db.query(SavedJob)
        .options(joinedload(SavedJob.job).joinedload(JobPost.company))
        .filter(SavedJob.id == saved.id)
        .first()
    )