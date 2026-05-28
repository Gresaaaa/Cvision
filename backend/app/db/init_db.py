from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Company, JobCategory, Permission, Role, RolePermission, Skill, User


DEFAULT_CATEGORIES = [
    ("Software Engineering", "Backend, frontend, and platform roles."),
    ("Data & AI", "Machine learning, analytics, and data platforms."),
    ("Product", "Product, design, and delivery management."),
    ("Sales & Marketing", "Commercial, growth, and brand roles."),
    ("Finance & Operations", "Accounting, operations, logistics, and procurement."),
    ("Customer Support", "Success, service, and support teams."),
    ("Education", "Teaching, training, and academic administration."),
    ("Healthcare", "Clinical, care, and healthcare administration roles."),
    ("Construction & Engineering", "Civil, mechanical, and field operations roles."),
    ("Human Resources", "Recruiting, people operations, and talent development."),
]

DEFAULT_SKILLS = [
    ("Python", "Backend"),
    ("FastAPI", "Backend"),
    ("React", "Frontend"),
    ("SQLAlchemy", "Backend"),
    ("PostgreSQL", "Database"),
    ("Redis", "Infrastructure"),
    ("JWT", "Security"),
    ("Docker", "Infrastructure"),
    ("CI/CD", "DevOps"),
    ("REST", "Backend"),
    ("Customer Service", "Service"),
    ("Communication", "Soft Skills"),
    ("Sales", "Commercial"),
    ("Negotiation", "Commercial"),
    ("Digital Marketing", "Marketing"),
    ("Content Writing", "Marketing"),
    ("Accounting", "Finance"),
    ("Financial Analysis", "Finance"),
    ("Operations Management", "Operations"),
    ("Inventory Management", "Operations"),
    ("Project Coordination", "Operations"),
    ("Teaching", "Education"),
    ("Curriculum Development", "Education"),
    ("Recruitment", "Human Resources"),
    ("Employee Relations", "Human Resources"),
    ("Patient Care", "Healthcare"),
    ("Clinical Documentation", "Healthcare"),
    ("AutoCAD", "Engineering"),
    ("Quality Assurance", "Manufacturing"),
    ("Microsoft Excel", "Office"),
]


def ensure_schema_upgrades() -> None:
    inspector = inspect(engine)
    if "notifications" not in inspector.get_table_names():
        notification_columns = set()
    else:
        notification_columns = {column["name"] for column in inspector.get_columns("notifications")}

    interview_columns = (
        {column["name"] for column in inspector.get_columns("interviews")}
        if "interviews" in inspector.get_table_names()
        else set()
    )
    company_columns = (
        {column["name"] for column in inspector.get_columns("companies")}
        if "companies" in inspector.get_table_names()
        else set()
    )
    candidate_profile_columns = (
        {column["name"] for column in inspector.get_columns("candidate_profiles")}
        if "candidate_profiles" in inspector.get_table_names()
        else set()
    )

    with engine.begin() as connection:
        if "notifications" in inspector.get_table_names() and "payload" not in notification_columns:
            connection.execute(text("ALTER TABLE notifications ADD COLUMN payload JSON"))
        if "interviews" in inspector.get_table_names() and "contact_email" not in interview_columns:
            connection.execute(text("ALTER TABLE interviews ADD COLUMN contact_email VARCHAR(255)"))
        if "interviews" in inspector.get_table_names() and "contact_phone" not in interview_columns:
            connection.execute(text("ALTER TABLE interviews ADD COLUMN contact_phone VARCHAR(40)"))
        if "companies" in inspector.get_table_names() and "logo_url" not in company_columns:
            connection.execute(text("ALTER TABLE companies ADD COLUMN logo_url VARCHAR(255)"))
        if "candidate_profiles" in inspector.get_table_names() and "avatar_url" not in candidate_profile_columns:
            connection.execute(text("ALTER TABLE candidate_profiles ADD COLUMN avatar_url VARCHAR(255)"))


def seed_base_data(db: Session) -> None:
    role_map: dict[str, Role] = {}
    for role_name in ROLE_PERMISSIONS:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name.title()} role")
            db.add(role)
            db.flush()
        role_map[role_name] = role

    permission_map: dict[str, Permission] = {}
    for permission_names in ROLE_PERMISSIONS.values():
        for permission_name in permission_names:
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            if not permission:
                permission = Permission(name=permission_name, description=permission_name.replace(":", " "))
                db.add(permission)
                db.flush()
            permission_map[permission_name] = permission

    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = role_map[role_name]
        existing_permission_ids = {
            item.permission_id for item in db.query(RolePermission).filter(RolePermission.role_id == role.id)
        }
        for permission_name in permission_names:
            permission = permission_map[permission_name]
            if permission.id not in existing_permission_ids:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    for name, description in DEFAULT_CATEGORIES:
        if not db.query(JobCategory).filter(JobCategory.name == name).first():
            db.add(JobCategory(name=name, description=description))

    for name, category in DEFAULT_SKILLS:
        if not db.query(Skill).filter(Skill.name == name).first():
            db.add(Skill(name=name, category=category))

    from app.core.config import get_settings

    settings = get_settings()
    admin = db.query(User).filter(User.email == settings.admin_email).first()
    if not admin:
        admin_role = role_map["admin"]
        admin = User(
            full_name="CVision Admin",
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password),
            role_id=admin_role.id,
            is_active=True,
        )
        db.add(admin)
        db.flush()

    demo_company = db.query(Company).filter(Company.name == "CVision Demo").first()
    if not demo_company:
        demo_company = Company(
            name="CVision Demo",
            description="Seed company for demos.",
            industry="Technology",
            location="Prishtina",
            owner_user_id=admin.id,
        )
        db.add(demo_company)
        db.flush()

    if admin.company_id != demo_company.id:
        admin.company_id = demo_company.id

    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_upgrades()
    db = SessionLocal()
    try:
        seed_base_data(db)
    finally:
        db.close()