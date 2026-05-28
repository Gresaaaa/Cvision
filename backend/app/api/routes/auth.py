from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import CandidateProfile, Company, Role, User
from app.schemas import AuthMessage, RegisterRequest, TokenResponse, UserPublic
from app.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not configured")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    if payload.role == "candidate":
        db.add(CandidateProfile(user_id=user.id, location=payload.location))
    else:
        company = Company(
            name=payload.company_name or f"{payload.full_name} Company",
            description=payload.company_description,
            industry=payload.industry,
            location=payload.location,
            owner_user_id=user.id,
        )
        db.add(company)
        db.flush()
        user.company_id = company.id

    audit_service.log(
        db,
        user_id=user.id,
        action="auth.register",
        entity_type="user",
        entity_id=str(user.id),
        company_id=user.company_id,
        details={"role": payload.role},
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .filter(User.id == user.id)
        .first()
    )
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .filter(User.email == form_data.username)
        .first()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated by an administrator")

    user.last_login_at = datetime.utcnow()
    audit_service.log(
        db,
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        company_id=user.company_id,
    )
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)), user=UserPublic.model_validate(user))


@router.post("/logout", response_model=AuthMessage)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit_service.log(
        db,
        user_id=current_user.id,
        action="auth.logout",
        entity_type="user",
        entity_id=str(current_user.id),
        company_id=current_user.company_id,
    )
    db.commit()
    return AuthMessage(message="Logout handled on client by deleting the JWT token.")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.company))
        .filter(User.id == current_user.id)
        .first()
    )
    return UserPublic.model_validate(user)
