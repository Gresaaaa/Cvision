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

    interview = Interview(
        application_id=application.id,
        scheduled_at=payload.scheduled_at,
        mode=payload.mode,
        location=payload.location,
        meeting_link=payload.meeting_link,
        notes=payload.notes,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )
    application.status = ApplicationStatus.INTERVIEW
    db.add(interview)
    db.flush()
    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            status=ApplicationStatus.INTERVIEW,
            changed_by_id=current_user.id,
            notes=payload.notes or "Interview invitation sent",
        )
    )
    audit_service.log(
        db,
        user_id=current_user.id,
        action="application.interview.invite",
        entity_type="interview",
        entity_id=str(interview.id),
        company_id=application.job.company_id,
        details={
            "application_id": application.id,
            "job_id": application.job_id,
            "candidate_id": application.candidate_id,
        },
    )
    db.commit()
    background_tasks.add_task(notify_application_status, application.id, ApplicationStatus.INTERVIEW.value)
    return interview


@router.get("/my", response_model=list[ApplicationPublic])
def my_applications(
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return (
        db.query(Application)
        .options(joinedload(Application.job).joinedload(JobPost.company), joinedload(Application.ai_score))
        .filter(Application.candidate_id == profile.id)
        .order_by(Application.applied_at.desc())
        .all()
    )


@router.patch("/{application_id}/status", response_model=ApplicationPublic)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .options(joinedload(Application.job), joinedload(Application.candidate).joinedload(CandidateProfile.user))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role.name == "company" and application.job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot update another company's application")

    application.status = payload.status
    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            status=payload.status,
            changed_by_id=current_user.id,
            notes=payload.notes,
        )
    )
    audit_service.log(
        db,
        user_id=current_user.id,
        action="application.status.update",
        entity_type="application",
        entity_id=str(application.id),
        company_id=application.job.company_id,
        details={"status": payload.status},
    )
    db.commit()
    background_tasks.add_task(notify_application_status, application.id, payload.status.value)
    return (
        db.query(Application)
        .options(joinedload(Application.job).joinedload(JobPost.company), joinedload(Application.ai_score))
        .filter(Application.id == application.id)
        .first()
    )