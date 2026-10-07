import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.platform import AuditLog


def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    actor_user_id: Optional[uuid.UUID] = None,
    entity_id: Optional[str] = None,
    ip: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Creates and records an audit log entry.
    """
    log_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip=ip,
        metadata_=metadata or {},
    )
    db.add(log_entry)
    db.commit()
    return log_entry
