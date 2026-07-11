import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core import crypto
from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Tests need a real encryption key regardless of what's (or isn't) in the
# local .env -- set one for the whole test session so brokerage tests are
# reproducible in CI/fresh clones without any manual setup.
settings.BROKERAGE_TOKEN_ENCRYPTION_KEY = Fernet.generate_key().decode()
crypto._fernet.cache_clear()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with TestSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

