"""
Audit Logger
Logs every action to the audit_logs Firestore collection.
"""

from datetime import datetime, timezone
from db import create_document


def log_action(
    user_id: str,
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    details: dict = None,
) -> str:
    """
    Create an audit log entry.
    
    Args:
        user_id: The ID of the user performing the action.
        action: Action type (e.g., 'user_registered', 'esg_analysis', 
                'scope3_analysis', 'carbon_gap', 'farmer_estimation',
                'matching', 'report_uploaded', 'profile_updated').
        entity_type: Type of entity affected (e.g., 'user', 'esg_report', 
                     'analysis_result', 'farmer_profile').
        entity_id: ID of the affected entity.
        details: Additional context as a dict (stored as JSONB/map).
    
    Returns:
        The audit log document ID.
    """
    log_data = {
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return create_document("audit_logs", log_data)
