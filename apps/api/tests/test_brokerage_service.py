import pytest

from app.core import crypto
from app.services.brokerage_service import BrokerageError, BrokerageNotConnectedError, BrokerageService

pytestmark = pytest.mark.asyncio


async def test_get_portfolio_before_connecting_raises(db_session):
    service = BrokerageService(db_session)
    with pytest.raises(BrokerageNotConnectedError):
        await service.get_portfolio(user_id="00000000-0000-0000-0000-000000000000")


async def test_start_connection_creates_encrypted_row(db_session):
    import uuid
    user_id = uuid.uuid4()

    service = BrokerageService(db_session)
    url = await service.start_connection(user_id)

    assert url  # stub provider returns a placeholder URL

    connection = await service.get_connection(user_id)
    assert connection is not None
    assert connection.status == "pending"
    # The stored secret must not be the plaintext -- it's encrypted at rest.
    decrypted = crypto.decrypt_secret(connection.encrypted_user_secret)
    assert connection.encrypted_user_secret != decrypted


async def test_start_connection_is_idempotent(db_session):
    import uuid
    user_id = uuid.uuid4()

    service = BrokerageService(db_session)
    await service.start_connection(user_id)
    first_connection = await service.get_connection(user_id)

    await service.start_connection(user_id)  # calling again shouldn't create a second row
    second_connection = await service.get_connection(user_id)

    assert first_connection.id == second_connection.id


async def test_get_portfolio_marks_connection_as_connected(db_session):
    import uuid
    user_id = uuid.uuid4()

    service = BrokerageService(db_session)
    await service.start_connection(user_id)

    connection_before = await service.get_connection(user_id)
    assert connection_before.status == "pending"

    portfolio = await service.get_portfolio(user_id)
    assert portfolio.holdings  # stub always returns at least 2 holdings

    connection_after = await service.get_connection(user_id)
    assert connection_after.status == "connected"


async def test_disconnect_removes_connection(db_session):
    import uuid
    user_id = uuid.uuid4()

    service = BrokerageService(db_session)
    await service.start_connection(user_id)
    await service.disconnect(user_id)

    connection = await service.get_connection(user_id)
    assert connection is None


async def test_disconnect_without_connection_raises(db_session):
    service = BrokerageService(db_session)
    with pytest.raises(BrokerageNotConnectedError):
        await service.disconnect(user_id="00000000-0000-0000-0000-000000000000")
