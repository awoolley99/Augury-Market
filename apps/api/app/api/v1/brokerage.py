from fastapi import APIRouter, Depends, HTTPException, status
from snaptrade_client.exceptions import OpenApiException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.crypto import EncryptionNotConfigured
from app.db.session import get_db
from app.models.user import User
from app.schemas.brokerage import (
    BrokerageConnectRead,
    BrokeragePortfolioRead,
    BrokerageStatusRead,
)
from app.services.brokerage_service import BrokerageError, BrokerageNotConnectedError, BrokerageService

router = APIRouter(prefix="/brokerage", tags=["brokerage"])


@router.get("/status", response_model=BrokerageStatusRead)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BrokerageService(db)
    connection = await service.get_connection(current_user.id)
    if not connection:
        return BrokerageStatusRead(connected=False)
    return BrokerageStatusRead(
        connected=connection.status == "connected",
        provider=connection.provider,
        status=connection.status,
        updated_at=connection.updated_at,
    )


@router.post("/connect", response_model=BrokerageConnectRead)
async def connect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Starts (or resumes) the brokerage-linking flow. Returns a URL to send
    the user to -- SnapTrade's hosted Connection Portal in production, a
    labeled placeholder when BROKERAGE_PROVIDER=stub. The user's actual
    brokerage login happens there, never on our servers.
    """
    service = BrokerageService(db)
    try:
        connect_url = await service.start_connection(current_user.id)
    except EncryptionNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuntimeError as exc:
        # e.g. BROKERAGE_PROVIDER=snaptrade but keys aren't configured
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OpenApiException as exc:
        # A real error FROM SnapTrade itself -- bad clientId/consumerKey,
        # a rejected request, etc. str(exc) includes SnapTrade's actual
        # status/reason/response body, which is exactly what's needed to
        # diagnose a real credentials/config problem.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SnapTrade rejected the request: {exc}",
        ) from exc
    return BrokerageConnectRead(connect_url=connect_url)


@router.get("/portfolio", response_model=BrokeragePortfolioRead)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BrokerageService(db)
    try:
        return await service.get_portfolio(current_user.id)
    except BrokerageNotConnectedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EncryptionNotConfigured, ValueError) as exc:
        # ValueError here specifically means decrypt_secret failed -- most
        # likely BROKERAGE_TOKEN_ENCRYPTION_KEY changed since this
        # connection's secret was encrypted.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OpenApiException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SnapTrade rejected the request: {exc}",
        ) from exc


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BrokerageService(db)
    try:
        await service.disconnect(current_user.id)
    except BrokerageNotConnectedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EncryptionNotConfigured, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OpenApiException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SnapTrade rejected the request: {exc}",
        ) from exc
