from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditService:
    def log(
        self,
        db: Session,
        *,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: str,
        company_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            company_id=company_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
        db.add(audit_log)
        db.flush()
        return audit_log


audit_service = AuditService()
