"""Simple encryption for API keys using Fernet (AES-128-CBC).

A machine-local key is derived from a secret file stored alongside the DB.
If the key file doesn't exist, one is generated automatically.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from config import DATA_DIR

_KEY_FILE = DATA_DIR / ".secret_key"


def _get_key() -> bytes:
    """Get or create a machine-local encryption key."""
    if _KEY_FILE.exists():
        raw = _KEY_FILE.read_bytes().strip()
    else:
        raw = Fernet.generate_key()
        _KEY_FILE.write_bytes(raw)
    # Ensure it's a valid 32-byte url-safe base64 key
    return raw


def _get_fernet() -> Fernet:
    return Fernet(_get_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a string, returning a base64-encoded ciphertext."""
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to plaintext."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        # If decryption fails (key changed, corrupted), return empty
        return ""
