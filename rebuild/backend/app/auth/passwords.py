"""Password hashing — stdlib only (pbkdf2)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 120_000
_ALGO = "sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        _ALGO, password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    ).hex()
    return f"pbkdf2_{_ALGO}${_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iters_s, salt, digest = password_hash.split("$", 3)
        if not scheme.startswith("pbkdf2_"):
            return False
        iters = int(iters_s)
        check = hashlib.pbkdf2_hmac(
            _ALGO, password.encode("utf-8"), salt.encode("utf-8"), iters
        ).hex()
        return hmac.compare_digest(check, digest)
    except (ValueError, TypeError):
        return False
