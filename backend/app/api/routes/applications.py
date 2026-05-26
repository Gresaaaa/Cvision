from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    CandidateProfile,
    Interview,
    JobPost,
    User,
)
from app.schemas import (
    ApplicationCreate,
    ApplicationPublic,
    ApplicationStatusUpdate,
    InterviewInviteRequest,
    InterviewPublic,
)
from app.services.audit_service import audit_service
from app.services.background_jobs import notify_application_status, process_application_scoring

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationPublic)
def apply_to_job(
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    job = db.query(JobPost).filter(JobPost.id == payload.job_id, JobPost.is_active.is_(True)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = (
        db.query(Application)
        .filter(Application.candidate_id == profile.id, Application.job_id == payload.job_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already applied to this job")

    application = Application(
        candidate_id=profile.id,
        job_id=payload.job_id,
        cover_letter=payload.cover_letter,
    )
    db.add(application)
    db.flush()
    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            status=application.status,
            changed_by_id=current_user.id,
            notes="Application submitted",
        )
    )
    audit_service.log(
        db,
        user_id=current_user.id,
        action="application.create",
        entity_type="application",
        entity_id=str(application.id),
        details={"job_id": payload.job_id},
    )
    db.commit()
    background_tasks.add_task(process_application_scoring, application.id)

    return (
        db.query(Application)
        .options(joinedload(Application.job).joinedload(JobPost.company), joinedload(Application.ai_score))
        .filter(Application.id == application.id)
        .first()
    )


@router.post("/{application_id}/invite-interview", response_model=InterviewPublic)
def invite_to_interview(
    application_id: int,
    payload: InterviewInviteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .options(
            joinedload(Application.job).joinedload(JobPost.company),
            joinedload(Application.candidate).joinedload(CandidateProfile.user),
            joinedload(Application.interviews),
        )
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role.name == "company" and application.job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot invite another company's candidate")
