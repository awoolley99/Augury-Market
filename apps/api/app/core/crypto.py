"""
Encryption for sensitive per-user tokens that must be stored at rest --
currently just each user's SnapTrade `userSecret` (functionally a per-user
API key that authorizes real brokerage account access on their behalf).

This is deliberately a separate key from SECRET_KEY (which signs JWTs):
rotating one should never require rotating the other, and a leak of one
shouldn't automatically compromise the other.
"""
from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class EncryptionNotConfigured(Exception):
    pass


@lru_cache
def _fernet() -> Fernet:
    if not settings.BROKERAGE_TOKEN_ENCRYPTION_KEY:
        raise EncryptionNotConfigured(
            "BROKERAGE_TOKEN_ENCRYPTION_KEY is not set. Generate one with:\n"
            "  python3 -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"\n"
            "and set it in your .env before connecting any brokerage account."
        )
    return Fernet(settings.BROKERAGE_TOKEN_ENCRYPTION_KEY.encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Could not decrypt stored brokerage secret -- BROKERAGE_TOKEN_ENCRYPTION_KEY "
            "may have changed since this was encrypted."
        ) from exc
