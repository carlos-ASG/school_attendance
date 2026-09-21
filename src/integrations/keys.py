import hashlib
import secrets
import string

KEY_ALPHABET = string.ascii_letters + string.digits
KEY_BODY_LENGTH = 43
KEY_TAG = 'dsk_'
KEY_PREFIX_LENGTH = 10


def generate_key() -> str:
    """Genera una key `dsk_<43 chars base62>` (~256 bits de entropía)."""
    body = ''.join(secrets.choice(KEY_ALPHABET) for _ in range(KEY_BODY_LENGTH))
    return f'{KEY_TAG}{body}'


def extract_prefix(key: str) -> str:
    """Prefijo de la key que se guarda indexado para lookup (~10 chars)."""
    return key[:KEY_PREFIX_LENGTH]


def hash_key(key: str) -> str:
    """SHA-256 hex de la key completa (el valor en claro nunca se persiste)."""
    return hashlib.sha256(key.encode('utf-8')).hexdigest()
