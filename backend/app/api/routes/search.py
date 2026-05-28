from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models import (
    Application,
    CandidateProfile,
    CandidateSkill,
    Education,
    EmploymentType,
    ExperienceLevel,
    JobMatchScore,
    JobPost,
    JobRequirement,
    Skill,
    WorkMode,
    User,
)
from app.schemas import CandidateSearchResult, JobPublic
from app.services.cache_service import cache_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/jobs", response_model=list[JobPublic])
def search_jobs(
    title: str | None = None,
    location: str | None = None,
    category_id: int | None = None,
    experience_level: ExperienceLevel | None = None,
    employment_type: EmploymentType | None = None,
    work_mode: WorkMode | None = None,
    db: Session = Depends(get_db),
):
    cache_key = f"search:jobs:{urlencode({k: v for k, v in locals().items() if k not in {'db'} and v is not None})}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached

    query = db.query(JobPost).options(
        joinedload(JobPost.company),
        joinedload(JobPost.category),
        joinedload(JobPost.requirements).joinedload(JobRequirement.skill),
    ).filter(JobPost.is_active.is_(True))
    if title:
        query = query.filter(JobPost.title.ilike(f"%{title}%"))
    if location:
        query = query.filter(JobPost.location.ilike(f"%{location}%"))
    if category_id:
        query = query.filter(JobPost.category_id == category_id)
    if experience_level:
        query = query.filter(JobPost.experience_level == experience_level)
    if employment_type:
        query = query.filter(JobPost.employment_type == employment_type)
    if work_mode:
        query = query.filter(JobPost.work_mode == work_mode)

    jobs = query.order_by(JobPost.created_at.desc()).all()
    encoded = jsonable_encoder([JobPublic.model_validate(job) for job in jobs])
    cache_service.set_json(cache_key, encoded)
    return jobs


@router.get("/candidates", response_model=list[CandidateSearchResult])
def search_candidates(
    skill: str | None = None,
    min_years_experience: int | None = None,
    education_keyword: str | None = None,
    min_score: float | None = None,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    query = db.query(CandidateProfile)
    if current_user.role.name == "company":
        query = query.join(Application).join(JobPost).filter(JobPost.company_id == current_user.company_id)
    if skill:
        query = query.join(CandidateSkill).join(Skill).filter(Skill.name.ilike(f"%{skill}%"))
    if min_years_experience is not None:
        query = query.filter(CandidateProfile.years_of_experience >= min_years_experience)
    if education_keyword:
        query = query.join(Education).filter(
            (Education.degree.ilike(f"%{education_keyword}%"))
            | (Education.field_of_study.ilike(f"%{education_keyword}%"))
        )
    if min_score is not None:
        query = query.join(Application).join(JobMatchScore).filter(JobMatchScore.score >= min_score)

    results = []
    for candidate in query.distinct().all():
        matched_skills = [
            link.skill.name for link in candidate.skills if link.skill and (not skill or skill.lower() in link.skill.name.lower())
        ]
        best_score = None
        for application in candidate.applications:
            if current_user.role.name == "company" and application.job.company_id != current_user.company_id:
                continue
            if application.ai_score:
                best_score = max(best_score or 0, application.ai_score.score)
        results.append(
            CandidateSearchResult(
                candidate_id=candidate.id,
                full_name=candidate.user.full_name,
                email=candidate.user.email,
                years_of_experience=candidate.years_of_experience,
                matched_skills=matched_skills,
                best_score=best_score,
            )
        )
    return results
