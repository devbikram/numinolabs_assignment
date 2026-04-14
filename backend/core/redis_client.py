"""
Lazy Redis client singleton.

Returns a connected ``redis.Redis`` instance when ``REDIS_URL`` is configured
and the server is reachable; otherwise returns ``None`` so callers can fall
back to an in-process alternative.
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client = None
_initialized = False


def get_redis():
    """Return a shared ``redis.Redis`` client, or ``None`` if Redis is unavailable."""
    global _client, _initialized

    # Fast-path: already resolved
    if _initialized:
        return _client

    with _lock:
        if _initialized:  # re-check inside lock
            return _client

        from config.settings import settings  # imported here to avoid circular deps

        if settings.REDIS_URL:
            try:
                import redis

                client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                client.ping()
                _client = client
                logger.info("Redis token blocklist enabled (%s)", settings.REDIS_URL)
            except Exception as exc:
                logger.error(
                    "Redis connection failed (%s) — falling back to in-process blocklist. "
                    "Token revocation will NOT be shared across workers.",
                    exc,
                )
                _client = None
        else:
            logger.warning(
                "REDIS_URL is not set — using in-process token blocklist. "
                "This is NOT suitable for multi-worker or multi-replica deployments."
            )
            _client = None

        _initialized = True

    return _client
