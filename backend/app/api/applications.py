# =============================================================================
# api/applications.py — Application Tracking Endpoints
# =============================================================================

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.application import Application
from app.schemas.application import ApplicationResponse, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get(
    "",
    response_model=list[ApplicationResponse],
    summary="List all applications",
)
async def list_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all job applications with optional status filtering."""
    
    query = select(Application).where(Application.user_id == current_user.id)
    
    if status_filter:
        query = query.where(Application.status == status_filter)
    
    query = query.order_by(Application.updated_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    apps = result.scalars().all()
    
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get(
    "/{app_id}",
    response_model=ApplicationResponse,
    summary="Get application details",
)
async def get_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific application."""
    
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return ApplicationResponse.model_validate(app)


@router.put(
    "/{app_id}",
    response_model=ApplicationResponse,
    summary="Update application status",
)
async def update_application(
    app_id: str,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually update an application's status or notes.
    
    The status_history is automatically updated to track all changes.
    """
    
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if data.status is not None:
        # Add to status history (audit trail)
        history = app.status_history or []
        history.append({
            "from": app.status,
            "to": data.status,
            "at": datetime.now(timezone.utc).isoformat(),
            "source": "manual",
        })
        app.status_history = history
        app.status = data.status
    
    if data.notes is not None:
        app.notes = data.notes
    
    if data.platform is not None:
        app.platform = data.platform
    
    db.add(app)
    await db.flush()
    
    return ApplicationResponse.model_validate(app)


@router.get(
    "/stats/analytics",
    summary="Get application analytics",
)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get application funnel analytics.
    
    Returns counts for each status stage — useful for the dashboard funnel chart.
    """
    
    result = await db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    )
    
    status_counts = {row[0]: row[1] for row in result.all()}
    total = sum(status_counts.values())
    
    return {
        "total_applications": total,
        "by_status": status_counts,
        "funnel": {
            "applied": status_counts.get("applied", 0),
            "under_review": status_counts.get("under_review", 0),
            "interview": status_counts.get("interview_scheduled", 0),
            "offer": status_counts.get("offer_received", 0),
            "rejected": status_counts.get("rejected", 0),
        },
    }


@router.delete(
    "/{app_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an application",
)
async def delete_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an application."""
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    await db.delete(app)
    await db.commit()
    
    return None

