import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import ApplicationStatus, EmploymentType, ExperienceLevel, WorkMode


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RolePublic(ORMModel):
    id: int
    name: str
    description: str | None = None


class CompanySummary(ORMModel):
    id: int
    name: str
    logo_url: str | None = None
    industry: str | None = None
    location: str | None = None


class SimpleUserPublic(ORMModel):
    id: int
    full_name: str
    email: EmailStr


class UserPublic(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    role: RolePublic
    company: CompanySummary | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["candidate", "company"]
    company_name: str | None = Field(default=None, min_length=2, max_length=120)
    company_description: str | None = Field(default=None, max_length=1000)
    industry: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)

    @field_validator("company_name", "company_description", "industry", "location", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None):
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must include at least one number")
        return value

    @model_validator(mode="after")
    def validate_company_fields(self):
        if self.role == "company" and not (self.company_name or "").strip():
            raise ValueError("Company name is required for company accounts")
        return self


class AuthMessage(BaseModel):
    message: str


class CandidateProfileUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    years_of_experience: int | None = None
    linkedin_url: str | None = Field(default=None, max_length=255)
    github_url: str | None = Field(default=None, max_length=255)
    desired_title: str | None = Field(default=None, max_length=120)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not re.fullmatch(r"\+?[0-9()\-\s]{7,20}", normalized):
            raise ValueError("Phone number format is invalid")
        return normalized


class CandidateProfilePublic(ORMModel):
    id: int
    phone: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    bio: str | None = None
    years_of_experience: int
    linkedin_url: str | None = None
    github_url: str | None = None
    desired_title: str | None = None
    user: SimpleUserPublic


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    website: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description", "industry", "location", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("Website must start with http:// or https://")
        return normalized


class CompanyPublic(ORMModel):
    id: int
    name: str
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    industry: str | None = None
    location: str | None = None
    owner_user_id: int | None = None
    is_active: bool
    created_at: datetime


class SkillCreate(BaseModel):
    name: str
    category: str | None = None


class SkillPublic(ORMModel):
    id: int
    name: str
    category: str | None = None


class CandidateSkillPublic(ORMModel):
    id: int
    level: str | None = None
    skill: SkillPublic | None = None


class JobCategoryCreate(BaseModel):
    name: str
    description: str | None = None


class JobCategoryPublic(ORMModel):
    id: int
    name: str
    description: str | None = None


class ResumePublic(ORMModel):
    id: int
    candidate_id: int
    file_url: str
    original_filename: str
    extracted_text: str
    version: int
    uploaded_at: datetime


class EducationPublic(ORMModel):
    id: int
    institution: str
    degree: str
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class ExperiencePublic(ORMModel):
    id: int
    company_name: str
    title: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class CertificationPublic(ORMModel):
    id: int
    name: str
    issuer: str | None = None
    issued_year: int | None = None


class LanguagePublic(ORMModel):
    id: int
    name: str
    proficiency: str | None = None


class CandidateProfileDetailPublic(CandidateProfilePublic):
    skills: list[CandidateSkillPublic] = []
    educations: list[EducationPublic] = []
    experiences: list[ExperiencePublic] = []
    certifications: list[CertificationPublic] = []
    languages: list[LanguagePublic] = []
    resumes: list[ResumePublic] = []


class AIAnalysisPublic(ORMModel):
    id: int
    resume_id: int | None = None
    application_id: int | None = None
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggested_improvements: list[str]
    extracted_skills: list[str]
    created_at: datetime


class JobRequirementPayload(BaseModel):
    skill_id: int | None = None
    skill_name: str | None = Field(default=None, max_length=120)
    required_level: str | None = None
    is_mandatory: bool = True

    @field_validator("skill_name", "required_level", mode="before")
    @classmethod
    def normalize_requirement_strings(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def validate_requirement_source(self):
        if self.skill_id is None and not (self.skill_name or "").strip():
            raise ValueError("Provide either an existing skill or a custom requirement")
        return self


class JobRequirementPublic(ORMModel):
    id: int
    required_level: str | None = None
    is_mandatory: bool
    skill: SkillPublic | None = None


class JobBase(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=20, max_length=6000)
    location: str = Field(min_length=2, max_length=120)
    category_id: int | None = None
    employment_type: EmploymentType
    work_mode: WorkMode = WorkMode.HYBRID
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    experience_level: ExperienceLevel
    requirements: list[JobRequirementPayload] = Field(default_factory=list)

    @field_validator("title", "description", "location", mode="before")
    @classmethod
    def normalize_job_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    category_id: int | None = None
    employment_type: EmploymentType | None = None
    work_mode: WorkMode | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    experience_level: ExperienceLevel | None = None
    is_active: bool | None = None
    requirements: list[JobRequirementPayload] | None = None

    @field_validator("title", "description", "location", mode="before")
    @classmethod
    def normalize_optional_job_strings(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value


class JobPublic(ORMModel):
    id: int
    title: str
    description: str
    location: str
    employment_type: EmploymentType
    work_mode: WorkMode
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    experience_level: ExperienceLevel
    is_active: bool
    created_at: datetime
    company: CompanySummary
    category: JobCategoryPublic | None = None
    requirements: list[JobRequirementPublic] = []


class JobMatchResult(ORMModel):
    id: int | None = None
    score: float
    explanation: str
    missing_skills: list[str]
    matched_skills: list[str]
    recommended_actions: list[str]
    created_at: datetime | None = None


class ApplicationCreate(BaseModel):
    job_id: int
    cover_letter: str | None = Field(default=None, max_length=5000)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    notes: str | None = None


class ApplicationPublic(ORMModel):
    id: int
    candidate_id: int
    job_id: int
    cover_letter: str | None = None
    status: ApplicationStatus
    applied_at: datetime
    candidate: CandidateProfilePublic | None = None
    job: JobPublic | None = None
    ai_score: JobMatchResult | None = None


class InterviewInviteRequest(BaseModel):
    scheduled_at: datetime | None = None
    mode: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    notes: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=40)

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not re.fullmatch(r"\+?[0-9()\-\s]{7,20}", normalized):
            raise ValueError("Contact phone number format is invalid")
        return normalized

    @model_validator(mode="after")
    def validate_contact_channel(self):
        if not self.contact_email and not self.contact_phone:
            raise ValueError("Provide at least a contact email or phone number for the interview")
        return self


class InterviewPublic(ORMModel):
    id: int
    application_id: int
    scheduled_at: datetime | None = None
    mode: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    notes: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class ApplicationWithInterviewPublic(ApplicationPublic):
    interviews: list[InterviewPublic] = []


class SavedJobPublic(ORMModel):
    id: int
    candidate_id: int
    job_id: int
    created_at: datetime
    job: JobPublic


class NotificationPublic(ORMModel):
    id: int
    title: str
    body: str
    notification_type: str
    payload: dict[str, Any] | None = None
    is_read: bool
    created_at: datetime


class DashboardStats(BaseModel):
    open_jobs: int
    active_applications: int
    unread_notifications: int
    saved_jobs: int | None = None
    resumes_uploaded: int | None = None
    companies: int | None = None


class CandidateSearchResult(BaseModel):
    candidate_id: int
    full_name: str
    email: EmailStr
    years_of_experience: int
    matched_skills: list[str]
    best_score: float | None = None


class CoverLetterResponse(BaseModel):
    job_id: int
    draft: str


class SystemOverview(BaseModel):
    total_users: int
    total_companies: int
    total_candidates: int
    total_jobs: int
    total_applications: int
    total_skills: int
    active_jobs: int
    unread_notifications: int


class AdminActionResponse(BaseModel):
    message: str
