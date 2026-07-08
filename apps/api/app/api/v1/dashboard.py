from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardBriefingRead
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/briefing", response_model=DashboardBriefingRead)
async def get_briefing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The morning briefing (Module 10): market overview, top opportunities
    across the whole scanned universe, the current user's watchlist summary
    (with day-over-day score deltas where available), and the most recently
    generated AI reports. Degrades to neutral/empty defaults if nothing has
    been scanned yet.
    """
    service = DashboardService(db)
    return await service.get_briefing(current_user.id)
