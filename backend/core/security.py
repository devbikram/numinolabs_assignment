import threading
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import settings
from core.redis_client import get_redis

# ---------------------------------------------------------------------------
# Token blocklist (logout / revocation)
# ---------------------------------------------------------------------------
# When REDIS_URL is configured the blocklist is stored in Redis with a TTL
# equal to the token's remaining lifetime, so every worker and replica shares
# the same view.  Without Redis the fallback is an in-process set — sufficient
# for a single-worker development server but NOT for production deployments
# that run multiple workers or container replicas.

_BLOCKLIST_PREFIX = "blocklist:"

# In-process fallback (used only when Redis is unavailable)
_bl_lock = threading.Lock()
_blocklist: set[str] = set()


def _ttl_from_exp(exp: int | None) -> int:
    """Return seconds until token expiry; minimum 1 second."""
    if exp is not None:
        remaining = exp - int(datetime.now(timezone.utc).timestamp())
        return max(1, remaining)
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def revoke_token(jti: str, exp: int | None = None) -> None:
    """Add *jti* to the blocklist.

    Pass the JWT ``exp`` claim so Redis can expire the key automatically once
    the token is no longer valid anyway (avoids unbounded key growth).
    """
    r = get_redis()
    if r is not None:
        r.set(f"{_BLOCKLIST_PREFIX}{jti}", "1", ex=_ttl_from_exp(exp))
    else:
        with _bl_lock:
            _blocklist.add(jti)


def is_token_revoked(jti: str) -> bool:
    r = get_redis()
    if r is not None:
        return r.exists(f"{_BLOCKLIST_PREFIX}{jti}") > 0
    with _bl_lock:
        return jti in _blocklist


def reset_blocklist() -> None:  # test-only helper
    # Clears the in-process fallback set.
    # When Redis is active its keys expire via TTL; tests never configure
    # REDIS_URL so this path is always the one exercised by the test suite.
    with _bl_lock:
        _blocklist.clear()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "jti": str(uuid.uuid4()), "token_type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        return None
