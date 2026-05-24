from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import JobCategory, Skill
from app.schemas import JobCategoryPublic, SkillPublic
from app.services.cache_service import cache_service

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])


@router.get("/skills", response_model=list[SkillPublic])
def get_skills(db: Session = Depends(get_db)):
    cached = cache_service.get_json("public:skills")
    if cached:
        return cached
    skills = db.query(Skill).order_by(Skill.name.asc()).all()
    cache_service.set_json("public:skills", jsonable_encoder(skills), ttl_seconds=1800)
    return skills


@router.get("/categories", response_model=list[JobCategoryPublic])
def get_categories(db: Session = Depends(get_db)):
    cached = cache_service.get_json("public:categories")
    if cached:
        return cached
    categories = db.query(JobCategory).order_by(JobCategory.name.asc()).all()
    cache_service.set_json("public:categories", jsonable_encoder(categories), ttl_seconds=1800)
    return categories
