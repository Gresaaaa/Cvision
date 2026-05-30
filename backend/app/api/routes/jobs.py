from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user, require_roles
from app.models import (
    Application,
    CandidateProfile,
    EmploymentType,
    ExperienceLevel,
    JobPost,
    JobRequirement,
    Skill,
    WorkMode,
    User,
)
from app.schemas import ApplicationWithInterviewPublic, JobCreate, JobPublic, JobUpdate
from app.services.audit_service import audit_service
from app.services.cache_service import cache_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _base_job_query(db: Session):
    return db.query(JobPost).options(
        joinedload(JobPost.company),
        joinedload(JobPost.category),
        joinedload(JobPost.requirements).joinedload(JobRequirement.skill),
    )


def _apply_job_filters(query, **filters):
    title = filters.get("title")
    location = filters.get("location")
    category_id = filters.get("category_id")
    min_salary = filters.get("min_salary")
    max_salary = filters.get("max_salary")
    experience_level = filters.get("experience_level")
    employment_type = filters.get("employment_type")
    work_mode = filters.get("work_mode")

    if title:
        query = query.filter(JobPost.title.ilike(f"%{title}%"))
    if location:
        query = query.filter(JobPost.location.ilike(f"%{location}%"))
    if category_id:
        query = query.filter(JobPost.category_id == category_id)
    if min_salary is not None:
        query = query.filter(JobPost.salary_min >= min_salary)
    if max_salary is not None:
        query = query.filter(JobPost.salary_max <= max_salary)
    if experience_level:
        query = query.filter(JobPost.experience_level == experience_level)
    if employment_type:
        query = query.filter(JobPost.employment_type == employment_type)
    if work_mode:
        query = query.filter(JobPost.work_mode == work_mode)
    return query


def _resolve_skill_id(db: Session, *, skill_id: int | None, skill_name: str | None) -> int:
    if skill_id is not None:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Selected skill not found")
        return skill.id

    normalized_name = (skill_name or "").strip()
    if not normalized_name:
        raise HTTPException(status_code=400, detail="A requirement must include an existing skill or a custom name")

    skill = db.query(Skill).filter(Skill.name.ilike(normalized_name)).first()
    if not skill:
        skill = Skill(name=normalized_name[:120], category="Custom")
        db.add(skill)
        db.flush()
    return skill.id


@router.post("", response_model=JobPublic)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Company account is not linked to a company")
    job = JobPost(
        company_id=current_user.company_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        category_id=payload.category_id,
        employment_type=payload.employment_type,
        work_mode=payload.work_mode,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        experience_level=payload.experience_level,
    )
    db.add(job)
    db.flush()
    for requirement in payload.requirements:
        resolved_skill_id = _resolve_skill_id(
            db,
            skill_id=requirement.skill_id,
            skill_name=requirement.skill_name,
        )
        db.add(
            JobRequirement(
                job_id=job.id,
                skill_id=resolved_skill_id,
                required_level=requirement.required_level,
                is_mandatory=requirement.is_mandatory,
            )
        )
    audit_service.log(
        db,
        user_id=current_user.id,
        action="job.create",
        entity_type="job_post",
        entity_id=str(job.id),
        company_id=current_user.company_id,
    )
    db.commit()
    cache_service.flush_prefix("jobs:")
    return _base_job_query(db).filter(JobPost.id == job.id).first()


@router.get("", response_model=list[JobPublic])
def list_jobs(
    title: str | None = None,
    location: str | None = None,
    category_id: int | None = None,
    min_salary: float | None = Query(default=None, ge=0),
    max_salary: float | None = Query(default=None, ge=0),
    experience_level: ExperienceLevel | None = None,
    employment_type: EmploymentType | None = None,
    work_mode: WorkMode | None = None,
    db: Session = Depends(get_db),
):
    cache_key = f"jobs:list:{urlencode({k: v for k, v in locals().items() if k not in {'db'} and v is not None})}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached

    query = _base_job_query(db).filter(JobPost.is_active.is_(True))
    query = _apply_job_filters(
        query,
        title=title,
        location=location,
        category_id=category_id,
        min_salary=min_salary,
        max_salary=max_salary,
        experience_level=experience_level,
        employment_type=employment_type,
        work_mode=work_mode,
    )
    jobs = query.order_by(JobPost.created_at.desc()).all()
    encoded = jsonable_encoder([JobPublic.model_validate(job) for job in jobs])
    cache_service.set_json(cache_key, encoded)
    return jobs


@router.get("/{job_id}", response_model=JobPublic)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = _base_job_query(db).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobPublic)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current_user.role.name == "company" and job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot edit another company's job")

    for field, value in payload.model_dump(exclude_unset=True, exclude={"requirements"}).items():
        setattr(job, field, value)

    if payload.requirements is not None:
        db.query(JobRequirement).filter(JobRequirement.job_id == job.id).delete()
        for requirement in payload.requirements:
            resolved_skill_id = _resolve_skill_id(
                db,
                skill_id=requirement.skill_id,
                skill_name=requirement.skill_name,
            )
            db.add(
                JobRequirement(
                    job_id=job.id,
                    skill_id=resolved_skill_id,
                    required_level=requirement.required_level,
                    is_mandatory=requirement.is_mandatory,
                )
            )

    audit_service.log(
        db,
        user_id=current_user.id,
        action="job.update",
        entity_type="job_post",
        entity_id=str(job.id),
        company_id=job.company_id,
    )
    db.commit()
    cache_service.flush_prefix("jobs:")
    return _base_job_query(db).filter(JobPost.id == job.id).first()


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current_user.role.name == "company" and job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot delete another company's job")
    job.is_active = False
    audit_service.log(
        db,
        user_id=current_user.id,
        action="job.delete",
        entity_type="job_post",
        entity_id=str(job.id),
        company_id=job.company_id,
    )
    db.commit()
    cache_service.flush_prefix("jobs:")
    return {"message": "Job deactivated"}


@router.get("/{job_id}/applications", response_model=list[ApplicationWithInterviewPublic])
def list_job_applications(
    job_id: int,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current_user.role.name == "company" and job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot access another company's applications")

    applications = (
        db.query(JobPost)
        .options(
            joinedload(JobPost.applications)
            .joinedload(Application.candidate)
            .joinedload(CandidateProfile.user),
            joinedload(JobPost.applications).joinedload(Application.ai_score),
            joinedload(JobPost.applications).joinedload(Application.interviews),
        )
        .filter(JobPost.id == job_id)
        .first()
    )
    if not applications:
        return []
    ranked = sorted(
        applications.applications,
        key=lambda item: item.ai_score.score if item.ai_score else 0,
        reverse=True,
    )
    return ranked
