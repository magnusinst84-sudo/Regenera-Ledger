"""
Audit Log Routes
View audit history for authenticated users.
"""

from fastapi import APIRouter, Depends, Query
from middleware.auth import get_current_user
from db import get_documents_by_field

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("/")
async def get_audit_logs(
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_current_user),
):
    """
    Get audit logs for the authenticated user.
    Returns the most recent logs first.
    """
    logs = get_documents_by_field(
        collection="audit_logs",
        field="user_id",
        value=user["id"],
        order_by="created_at",
        order_desc=True,
        limit=limit,
    )
    return {"logs": logs, "count": len(logs)}
