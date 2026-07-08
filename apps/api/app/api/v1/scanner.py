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
    filter to specific tickers (e.g. a user's watchlist) -- any ticker not
    yet scanned gets scanned on demand, so this works for any ticker, not
    just ones in the pre-scanned sample universe. Omit `tickers` to get
    every ticker the scanner has ever processed, with no on-demand scanning
    (there's no specific ticker being asked for in that case).
    """
    repo = EvidenceRepository(db)
    if tickers:
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        scanner = ScannerService(db)
        packets = []
        for ticker in ticker_list:
            try:
                packets.append(await scanner.ensure_scanned(ticker))
            except ValueError:
                continue  # invalid ticker for the current provider -- skip, don't fail the whole list
        return packets
    return await repo.list_all_latest()


@router.get("/evidence/{ticker}", response_model=EvidencePacketRead)
async def get_evidence(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scanner = ScannerService(db)
    try:
        return await scanner.ensure_scanned(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
