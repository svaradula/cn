"""
redis_cache.py — Async Redis cache wrapper.
Used to cache NAV data, recommendations, and session profiles.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        value = await r.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning("Cache GET failed for %s: %s", key, e)
    return None


async def cache_set(key: str, value: Any, ttl: int) -> bool:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning("Cache SET failed for %s: %s", key, e)
        return False


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning("Cache DELETE failed for %s: %s", key, e)


# ── Typed Helpers ────────────────────────────────────────────────────────────

async def get_user_profile(user_id: str) -> Optional[dict]:
    return await cache_get(f"profile:{user_id}")


async def set_user_profile(user_id: str, profile: dict) -> None:
    await cache_set(f"profile:{user_id}", profile, ttl=86400)  # 24 hours


async def get_nav_cache(scheme_code: str) -> Optional[dict]:
    return await cache_get(f"nav:{scheme_code}")


async def set_nav_cache(scheme_code: str, nav_data: dict) -> None:
    await cache_set(f"nav:{scheme_code}", nav_data, ttl=settings.nav_cache_ttl)


async def get_recommendations_cache(user_id: str) -> Optional[list]:
    return await cache_get(f"recs:{user_id}")


async def set_recommendations_cache(user_id: str, recs: list) -> None:
    await cache_set(f"recs:{user_id}", recs, ttl=settings.recs_cache_ttl)


async def get_all_funds_cache() -> Optional[list]:
    return await cache_get("funds:all")


async def set_all_funds_cache(funds: list) -> None:
    await cache_set("funds:all", funds, ttl=settings.nav_cache_ttl)