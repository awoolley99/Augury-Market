from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.confidence import ConfidenceRead
from app.services.confidence import compute_confidence

router = APIRouter(prefix="/confidence", tags=["confidence"])


@router.get("/{ticker}", response_model=ConfidenceRead)
async def get_confidence(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = EvidenceRepository(db)
    packet = await repo.get_latest(ticker)
    if not packet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evidence packet found for {ticker.upper()}. Run a scan first.",
        )
    result = compute_confidence(packet)
    return ConfidenceRead(
        ticker=result.ticker,
        total_score=result.total_score,
        recommendation=result.recommendation,
        dimensions=[d.__dict__ for d in result.dimensions],
        risk_adjustment_points=result.risk_adjustment_points,
        strengths=result.strengths,
        risks=result.risks,
    )


@router.get("", response_model=list[ConfidenceRead])
async def list_confidence(
    tickers: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = EvidenceRepository(db)
    if tickers:
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        packets = await repo.list_latest_for_tickers(ticker_list)
    else:
        packets = await repo.list_all_latest()

    results = []
    for packet in packets:
        result = compute_confidence(packet)
        results.append(
            ConfidenceRead(
                ticker=result.ticker,
                total_score=result.total_score,
                recommendation=result.recommendation,
                dimensions=[d.__dict__ for d in result.dimensions],
                risk_adjustment_points=result.risk_adjustment_points,
                strengths=result.strengths,
                risks=result.risks,
            )
        )
    return results
