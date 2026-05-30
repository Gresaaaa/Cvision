from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import get_settings
from app.models import Company, User
from app.schemas import CompanyPublic, CompanyUpdate
from app.services.audit_service import audit_service
from app.services.media_service import media_service

router = APIRouter(tags=["Companies"])
settings = get_settings()


@router.get("/companies/{company_id}", response_model=CompanyPublic)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/companies/me", response_model=CompanyPublic)
def get_my_company(
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return company


@router.put("/companies/me", response_model=CompanyPublic)
def update_my_company(
    payload: CompanyUpdate,
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    audit_service.log(
        db,
        user_id=current_user.id,
        action="company.profile.update",
        entity_type="company",
        entity_id=str(company.id),
        company_id=company.id,
    )
    db.commit()
    db.refresh(company)
    return company


@router.post("/companies/me/logo", response_model=CompanyPublic)
def upload_company_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("company", "admin")),
    db: Session = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")

    media_service.delete_uploaded_file(company.logo_url, settings.upload_dir)
    company.logo_url = media_service.save_image(file, settings.upload_dir, "logos")
    audit_service.log(
        db,
        user_id=current_user.id,
        action="company.profile.logo.upload",
        entity_type="company",
        entity_id=str(company.id),
        company_id=company.id,
    )
    db.commit()
    db.refresh(company)
    return company
