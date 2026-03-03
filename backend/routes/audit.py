"""
Audit Log Routes
View audit history for authenticated users.
"""

import logging
from fastapi import APIRouter, Depends, Query
from middleware.auth import get_current_user
from db import get_documents_by_field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("/")
async def get_audit_logs(
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_current_user),
):
    """
    Get audit logs for the authenticated user.
    Returns the most recent logs first.
    Gracefully handles missing Firestore index by returning empty list.
    """
    try:
        logs = get_documents_by_field(
            collection="audit_logs",
            field="user_id",
            value=user["id"],
            order_by="created_at",
            order_desc=True,
            limit=limit,
        )
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        err = str(e)
        # Firestore composite index not yet built — return empty gracefully
        if "requires an index" in err or "FAILED_PRECONDITION" in err:
            logger.warning("audit_logs index missing — returning empty. Create it in Firebase Console.")
            return {
                "logs": [],
                "count": 0,
                "notice": "Audit index is being built. Please wait a minute and refresh.",
            }
        raise
