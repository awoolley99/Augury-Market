import pytest

from app.core import crypto


def test_encrypt_decrypt_round_trip():
    plaintext = "super-secret-snaptrade-user-secret"
    ciphertext = crypto.encrypt_secret(plaintext)
    assert ciphertext != plaintext
    assert crypto.decrypt_secret(ciphertext) == plaintext


def test_ciphertext_is_not_plaintext_substring():
    plaintext = "obviously-sensitive-value-12345"
    ciphertext = crypto.encrypt_secret(plaintext)
    assert plaintext not in ciphertext


def test_tampered_ciphertext_fails_to_decrypt():
    plaintext = "another-secret"
    ciphertext = crypto.encrypt_secret(plaintext)
    tampered = ciphertext[:-4] + "abcd"
    with pytest.raises(ValueError, match="Could not decrypt"):
        crypto.decrypt_secret(tampered)


def test_missing_key_raises_clear_error(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "BROKERAGE_TOKEN_ENCRYPTION_KEY", None)
    crypto._fernet.cache_clear()
    try:
        with pytest.raises(crypto.EncryptionNotConfigured):
            crypto.encrypt_secret("x")
    finally:
        crypto._fernet.cache_clear()
