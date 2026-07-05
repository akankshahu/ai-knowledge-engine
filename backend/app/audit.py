import json
from datetime import datetime
from sqlalchemy.orm import Session
from . import models


def log_audit(db: Session, user_id: str, tenant_id: str, action: str, resource: str, details: dict = None):
    """
    Log an audit event: who did what on what resource in which tenant.
    
    Args:
        db: SQLAlchemy session
        user_id: ID of user performing action
        tenant_id: ID of tenant
        action: Action type (e.g., "UPLOAD", "QUERY", "DELETE")
        resource: Resource identifier (e.g., document_id)
        details: Optional extra metadata
    """
    try:
        # Placeholder: in production, store in separate audit table or logs
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "action": action,
            "resource": resource,
            "details": details or {},
        }
        print(f"[AUDIT] {json.dumps(audit_record)}")
    except Exception as e:
        print(f"[AUDIT_ERROR] {e}")


def enforce_tenant_isolation(tenant_id: str, resource_tenant_id: str):
    """Verify that user's tenant matches resource's tenant."""
    if tenant_id != resource_tenant_id:
        raise PermissionError(f"Tenant mismatch: {tenant_id} != {resource_tenant_id}")
