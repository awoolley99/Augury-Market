from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.ai_summary import AISummaryRead
from app.services.ai_summary_service import AISummaryService

router = APIRouter(prefix="/summary", tags=["ai-summary"])


@router.get("/{ticker}", response_model=AISummaryRead)
async def get_summary(
    ticker: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns today's AI summary for a ticker, generating (and caching) one if
    it doesn't exist yet. Pass ?force=true to regenerate even if a cached
    summary already exists for today (e.g. after a fresh scan).
    """
    evidence_repo = EvidenceRepository(db)
    packet = await evidence_repo.get_latest(ticker)
    if not packet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evidence packet found for {ticker.upper()}. Run a scan first.",
        )

    service = AISummaryService(db)
    try:
        summary = await service.get_or_generate(packet, force=force)
    except RuntimeError as exc:
        # e.g. AI_SUMMARY_PROVIDER=anthropic but ANTHROPIC_API_KEY isn't set
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return summary
