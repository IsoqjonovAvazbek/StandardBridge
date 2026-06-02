from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    key = settings.FERNET_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_card(value: str) -> str:
    """Fernet bilan karta raqamini shifrlaydi. Bo'sh yoki allaqachon shifrlangan bo'lsa — o'zgartirmaydi."""
    if not value or _is_encrypted(value):
        return value
    return _fernet().encrypt(value.encode()).decode()


def decrypt_card(value: str) -> str:
    """Shifrlangan karta raqamini ochadi. Ochilmagan (eski ma'lumot) bo'lsa — as-is qaytaradi."""
    if not value or not _is_encrypted(value):
        return value
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return value


def _is_encrypted(value: str) -> bool:
    # Fernet tokenlar har doim 'gAAAAA' (version 0x80, base64) bilan boshlanadi
    return value.startswith('gAAAAA')
