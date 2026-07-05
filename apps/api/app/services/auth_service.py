import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair, UserCreate, UserLogin


class AuthError(Exception):
    """Raised for any client-facing auth failure (bad creds, duplicate email, etc.)."""


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def register(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise AuthError("An account with this email already exists")

        user = await self.users.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        await self.session.commit()
        return user

    async def authenticate(self, payload: UserLogin) -> User:
        user = await self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise AuthError("Incorrect email or password")
        if not user.is_active:
            raise AuthError("This account has been deactivated")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        subject = str(user.id)
        return TokenPair(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            subject = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise AuthError(str(exc)) from exc

        user = await self.users.get_by_id(uuid.UUID(subject))
        if not user or not user.is_active:
            raise AuthError("Account no longer valid")

        return self.issue_tokens(user)
