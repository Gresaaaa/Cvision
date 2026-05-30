from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class WorkMode(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission", cascade="all, delete-orphan"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), index=True)

    role: Mapped["Role"] = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped["Role"] = relationship(back_populates="users")
    company: Mapped["Company | None"] = relationship(
        "Company", back_populates="users", foreign_keys=[company_id]
    )
    owned_company: Mapped["Company | None"] = relationship(
        "Company", back_populates="owner", uselist=False, foreign_keys="Company.owner_user_id"
    )
    candidate_profile: Mapped["CandidateProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    owner: Mapped["User | None"] = relationship(
        "User", back_populates="owned_company", foreign_keys=[owner_user_id]
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company", foreign_keys="User.company_id"
    )
    jobs: Mapped[list["JobPost"]] = relationship(back_populates="company")


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_of_experience: Mapped[int] = mapped_column(Integer, default=0)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    desired_title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    user: Mapped["User"] = relationship(back_populates="candidate_profile")
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    skills: Mapped[list["CandidateSkill"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    educations: Mapped[list["Education"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    languages: Mapped[list["Language"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    saved_jobs: Mapped[list["SavedJob"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    file_url: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    extracted_text: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="resumes")
    sections: Mapped[list["ResumeSection"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AIAnalysis"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeSection(Base):
    __tablename__ = "resume_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    section_name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    resume: Mapped["Resume"] = relationship(back_populates="sections")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)

    candidate_links: Mapped[list["CandidateSkill"]] = relationship(back_populates="skill")
    job_requirements: Mapped[list["JobRequirement"]] = relationship(back_populates="skill")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="candidate_links")


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    institution: Mapped[str] = mapped_column(String(150))
    degree: Mapped[str] = mapped_column(String(150))
    field_of_study: Mapped[str | None] = mapped_column(String(150), nullable=True)
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="educations")


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    company_name: Mapped[str] = mapped_column(String(150))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(30), nullable=True)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="experiences")


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    issuer: Mapped[str | None] = mapped_column(String(150), nullable=True)
    issued_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="certifications")


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    proficiency: Mapped[str | None] = mapped_column(String(60), nullable=True)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="languages")


class JobCategory(Base):
    __tablename__ = "job_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    jobs: Mapped[list["JobPost"]] = relationship(back_populates="category")


class JobPost(Base):
    __tablename__ = "job_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("job_categories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(120))
    employment_type: Mapped[EmploymentType] = mapped_column(SQLEnum(EmploymentType))
    work_mode: Mapped[WorkMode] = mapped_column(SQLEnum(WorkMode), default=WorkMode.HYBRID)
    salary_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    experience_level: Mapped[ExperienceLevel] = mapped_column(SQLEnum(ExperienceLevel))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="jobs")
    category: Mapped["JobCategory | None"] = relationship(back_populates="jobs")
    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    required_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    job: Mapped["JobPost"] = relationship(back_populates="requirements")
    skill: Mapped["Skill"] = relationship(back_populates="job_requirements")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_application"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id"), index=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus), default=ApplicationStatus.SUBMITTED
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="applications")
    job: Mapped["JobPost"] = relationship(back_populates="applications")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    ai_score: Mapped["JobMatchScore | None"] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AIAnalysis"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus))
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="status_history")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True, index=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    suggested_improvements: Mapped[list] = mapped_column(JSON, default=list)
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    resume: Mapped["Resume | None"] = relationship(back_populates="analyses")
    application: Mapped["Application | None"] = relationship(back_populates="analyses")


class JobMatchScore(Base):
    __tablename__ = "job_match_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True, index=True)
    score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="ai_score")


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_saved_job"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    candidate: Mapped["CandidateProfile"] = relationship(back_populates="saved_jobs")
    job: Mapped["JobPost"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    body: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(60), default="info")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mode: Mapped[str | None] = mapped_column(String(60), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="interviews")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(150), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[str] = mapped_column(String(120))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
