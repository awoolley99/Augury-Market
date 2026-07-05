from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.evidence import EvidencePacketRead, ScanRunResult
from app.services.scanner import ScannerService

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.post("/run", response_model=ScanRunResult)
async def run_scan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the Stock Scanner Engine over the full universe synchronously.
    Fine for the sample universe (~40 tickers) and the stub provider; once
    a real market data vendor and a 1,000+ ticker universe are in place,
    this moves to a background worker (Module 6 note in the product brief).
    """
    scanner = ScannerService(db)
    result = await scanner.scan_universe()
    return ScanRunResult(
        as_of_date=date.today(),
        processed_count=len(result.processed),
        failed_count=len(result.failed),
        processed=result.processed,
        failed=[f"{ticker}: {reason}" for ticker, reason in result.failed],
    )


@router.get("/evidence", response_model=list[EvidencePacketRead])
async def list_evidence(
    tickers: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List the latest evidence packet per ticker. Pass `?tickers=NVDA,AMD` to
    filter to specific tickers (e.g. a user's watchlist); omit it to get
    every ticker the scanner has ever processed.
    """
    repo = EvidenceRepository(db)
    if tickers:
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        return await repo.list_latest_for_tickers(ticker_list)
    return await repo.list_all_latest()


@router.get("/evidence/{ticker}", response_model=EvidencePacketRead)
async def get_evidence(
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
    return packet
