from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models import AIAnalysis, Application, CandidateProfile, CandidateSkill, JobPost, JobRequirement, JobMatchScore, Resume, User
from app.schemas import AIAnalysisPublic, CoverLetterResponse, JobMatchResult
from app.services.ai_service import ai_service
from app.services.audit_service import audit_service
from app.services.background_jobs import process_application_scoring, process_resume_analysis
from app.services.cache_service import cache_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/analyze-resume", response_model=AIAnalysisPublic)
def analyze_resume(
    resume_id: int | None = None,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    query = db.query(Resume).filter(Resume.candidate_id == profile.id)
    if resume_id:
        query = query.filter(Resume.id == resume_id)
    resume = query.order_by(Resume.version.desc()).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    process_resume_analysis(resume.id)
    analysis = db.query(AIAnalysis).filter(AIAnalysis.resume_id == resume.id).first()
    cache_service.set_json(f"ai:resume:{resume.id}", jsonable_encoder(AIAnalysisPublic.model_validate(analysis)))
    audit_service.log(
        db,
        user_id=current_user.id,
        action="ai.resume.analyze",
        entity_type="resume",
        entity_id=str(resume.id),
    )
    db.commit()
    return analysis


@router.get("/resume-analysis/{resume_id}", response_model=AIAnalysisPublic)
def get_resume_analysis(
    resume_id: int,
    current_user: User = Depends(require_roles("candidate", "company", "admin")),
    db: Session = Depends(get_db),
):
    cached = cache_service.get_json(f"ai:resume:{resume_id}")
    if cached:
        return cached
    analysis = db.query(AIAnalysis).filter(AIAnalysis.resume_id == resume_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if current_user.role.name == "candidate":
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        if not profile or resume.candidate_id != profile.id:
            raise HTTPException(status_code=403, detail="Not allowed to view this analysis")
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
            raise HTTPException(status_code=403, detail="Not allowed to view this analysis")
    cache_service.set_json(f"ai:resume:{resume_id}", jsonable_encoder(AIAnalysisPublic.model_validate(analysis)))
    return analysis


@router.post("/job-match/{job_id}", response_model=JobMatchResult)
def preview_job_match(
    job_id: int,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfile)
        .options(
            joinedload(CandidateProfile.skills).joinedload(CandidateSkill.skill),
            joinedload(CandidateProfile.resumes),
        )
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    job = (
        db.query(JobPost)
        .options(joinedload(JobPost.requirements).joinedload(JobRequirement.skill))
        .filter(JobPost.id == job_id, JobPost.is_active.is_(True))
        .first()
    )
    if not profile or not profile.resumes:
        raise HTTPException(status_code=400, detail="Upload a resume first")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    latest_resume = sorted(profile.resumes, key=lambda item: item.version, reverse=True)[0]
    candidate_skills = [link.skill.name for link in profile.skills if link.skill]
    result = ai_service.calculate_job_match(
        resume_text=latest_resume.extracted_text,
        candidate_skills=candidate_skills,
        job=job,
    )
    return JobMatchResult.model_validate(result)


@router.get("/application-score/{application_id}", response_model=JobMatchResult)
def get_application_score(
    application_id: int,
    current_user: User = Depends(require_roles("candidate", "company", "admin")),
    db: Session = Depends(get_db),
):
    cached = cache_service.get_json(f"ai:application:{application_id}")
    if cached:
        return cached

    application = (
        db.query(Application)
        .options(joinedload(Application.job), joinedload(Application.candidate).joinedload(CandidateProfile.user))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role.name == "candidate" and application.candidate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this score")
    if current_user.role.name == "company" and application.job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not allowed to view this score")

    score = db.query(JobMatchScore).filter(JobMatchScore.application_id == application_id).first()
    if not score:
        process_application_scoring(application_id)
        score = db.query(JobMatchScore).filter(JobMatchScore.application_id == application_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not available")
    encoded = jsonable_encoder(JobMatchResult.model_validate(score))
    cache_service.set_json(f"ai:application:{application_id}", encoded)
    return score


@router.post("/cover-letter/{job_id}", response_model=CoverLetterResponse)
def generate_cover_letter(
    job_id: int,
    current_user: User = Depends(require_roles("candidate")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CandidateProfile)
        .options(joinedload(CandidateProfile.resumes), joinedload(CandidateProfile.user))
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    job = (
        db.query(JobPost)
        .options(joinedload(JobPost.company))
        .filter(JobPost.id == job_id, JobPost.is_active.is_(True))
        .first()
    )
    if not profile or not profile.resumes:
        raise HTTPException(status_code=400, detail="Upload a resume first")
    if not job or not job.company:
        raise HTTPException(status_code=404, detail="Job not found")

    latest_resume = sorted(profile.resumes, key=lambda item: item.version, reverse=True)[0]
    analysis = db.query(AIAnalysis).filter(AIAnalysis.resume_id == latest_resume.id).first()
    summary = analysis.summary if analysis else "I bring relevant experience and a strong motivation to contribute."
    draft = ai_service.generate_cover_letter(
        candidate_name=profile.user.full_name,
        company_name=job.company.name,
        job_title=job.title,
        summary=summary,
    )
    return CoverLetterResponse(job_id=job_id, draft=draft)
