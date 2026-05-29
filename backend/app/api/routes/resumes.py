from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import get_settings
from app.models import Application, CandidateProfile, JobPost, Resume, User
from app.schemas import ResumePublic
from app.services.audit_service import audit_service
from app.services.background_jobs import process_resume_analysis
from app.services.resume_service import resume_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])
settings = get_settings()


def _get_allowed_resume(resume_id: int, current_user: User, db: Session) -> Resume:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if current_user.role.name == "candidate":
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        if not profile or resume.candidate_id != profile.id:
            raise HTTPException(status_code=403, detail="Not allowed to view this resume")
    if current_user.role.name == "company":
        allowed = (
            db.query(Application)
            .join(JobPost, JobPost.id == Application.job_id)
            .filter(
                Application.candidate_id == resume.candidate_id,
                JobPost.company_id == current_user.company_id,
            )
            .first()
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Not allowed to view this resume")
    return resume


@router.post("/upload", response_model=ResumePublic)
def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    destination = resume_service.save_upload(file, settings.upload_dir)
    extracted_text = resume_service.extract_text(destination)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Unable to extract text from this file")

    version = (db.query(Resume).filter(Resume.candidate_id == profile.id).count() or 0) + 1
    resume = Resume(
        candidate_id=profile.id,
        file_url=f"/uploads/{destination.name}",
        original_filename=file.filename or destination.name,
        extracted_text=extracted_text,
        version=version,
    )
    db.add(resume)
    db.flush()
    resume_service.create_sections(db, resume, extracted_text)
    audit_service.log(
        db,
        user_id=current_user.id,
        action="resume.upload",
        entity_type="resume",
        entity_id=str(resume.id),
    )
    db.commit()
    db.refresh(resume)

    background_tasks.add_task(process_resume_analysis, resume.id)
    return resume


@router.get("/my", response_model=list[ResumePublic])
def my_resumes(
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return (
        db.query(Resume)
        .filter(Resume.candidate_id == profile.id)
        .order_by(Resume.version.desc())
        .all()
    )


@router.get("/{resume_id}", response_model=ResumePublic)
def get_resume(
    resume_id: int,
    current_user: User = Depends(require_roles("candidate", "company", "admin")),
    db: Session = Depends(get_db),
):
    return _get_allowed_resume(resume_id, current_user, db)


@router.get("/{resume_id}/file")
def view_resume_file(
    resume_id: int,
    current_user: User = Depends(require_roles("candidate", "company", "admin")),
    db: Session = Depends(get_db),
):
    resume = _get_allowed_resume(resume_id, current_user, db)
    file_name = Path(resume.file_url).name
    file_path = Path(settings.upload_dir) / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found")
    media_type = "application/octet-stream"
    if file_path.suffix.lower() == ".pdf":
        media_type = "application/pdf"
    elif file_path.suffix.lower() == ".docx":
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    elif file_path.suffix.lower() == ".txt":
        media_type = "text/plain"
    return FileResponse(path=file_path, media_type=media_type)


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not profile or not resume or resume.candidate_id != profile.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    audit_service.log(
        db,
        user_id=current_user.id,
        action="resume.delete",
        entity_type="resume",
        entity_id=str(resume.id),
    )
    db.commit()

    file_name = Path(resume.file_url).name
    file_path = Path(settings.upload_dir) / file_name
    if file_path.exists():
        file_path.unlink()
    return {"message": "Resume deleted"}
