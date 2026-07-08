from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_summary import AISummaryRead
from app.services.ai_summary_service import AISummaryService
from app.services.scanner import ScannerService

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
    it doesn't exist yet. The ticker itself is also scanned on demand if it
    hasn't been already. Pass ?force=true to regenerate the summary even if
    a cached one already exists for today (e.g. after a fresh scan).
    """
    scanner = ScannerService(db)
    try:
        packet = await scanner.ensure_scanned(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    service = AISummaryService(db)
    try:
        summary = await service.get_or_generate(packet, force=force)
    except RuntimeError as exc:
        # e.g. AI_SUMMARY_PROVIDER=anthropic but ANTHROPIC_API_KEY isn't set
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return summary
