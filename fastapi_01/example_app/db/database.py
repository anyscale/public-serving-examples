import json
import hashlib
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
import numpy as np
from example_app.config import REDIS_URI


# Custom JSON encoder to handle NumPy data types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


# Global redis connection pool
redis_pool = None


async def get_redis() -> redis.Redis:
    """Get Redis connection."""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(REDIS_URI)
    return redis.Redis(connection_pool=redis_pool)


async def close_redis():
    """Close Redis connection pool."""
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None


async def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    """Get cached response from Redis."""
    r = await get_redis()
    cached = await r.get(key)
    if cached:
        return json.loads(cached)
    return None


async def set_cached_response(key: str, data: Dict[str, Any], expire: int = 300):
    """Set cached response in Redis."""
    r = await get_redis()
    await r.setex(key, expire, json.dumps(data, cls=NumpyEncoder))


async def generate_cache_key(prefix: str, content: str) -> str:
    """Generate a cache key for a given content."""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}:{content_hash}"


async def increment_rate_limit(client_ip: str) -> int:
    """Increment rate limit counter for client IP."""
    r = await get_redis()
    key = f"ratelimit:{client_ip}"

    # Increment counter
    current = await r.incr(key)

    # Set expiry if it's a new key
    if current == 1:
        await r.expire(key, 60)  # 1 minute expiry

    return current


async def get_rate_limit(client_ip: str) -> int:
    """Get current rate limit counter for client IP."""
    r = await get_redis()
    key = f"ratelimit:{client_ip}"
    value = await r.get(key)
    return int(value) if value else 0


async def store_request_history(
    user_id: str, endpoint: str, request_data: Dict[str, Any]
) -> str:
    """Store request history in Redis."""
    r = await get_redis()
    request_id = hashlib.md5(
        f"{user_id}:{endpoint}:{json.dumps(request_data)}".encode()
    ).hexdigest()
    key = f"history:{user_id}:{request_id}"

    history_data = {
        "request_id": request_id,
        "user_id": user_id,
        "endpoint": endpoint,
        "request_data": request_data,
        "timestamp": (await r.time())[0],  # Unix timestamp
    }

    await r.set(key, json.dumps(history_data))
    await r.expire(key, 86400 * 7)  # Keep for 7 days

    # Add to user's history list
    await r.lpush(f"user:{user_id}:history", request_id)
    await r.ltrim(f"user:{user_id}:history", 0, 99)  # Keep last 100 requests

    return request_id


async def get_request_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's request history."""
    r = await get_redis()

    # Get list of request IDs
    request_ids = await r.lrange(f"user:{user_id}:history", 0, limit - 1)

    if not request_ids:
        return []

    # Get request details
    history = []
    for request_id in request_ids:
        request_id_str = (
            request_id.decode() if isinstance(request_id, bytes) else request_id
        )
        data = await r.get(f"history:{user_id}:{request_id_str}")
        if data:
            history.append(json.loads(data))

    return history


async def delete_request_history(user_id: str, request_id: str) -> bool:
    """Delete a request from history."""
    r = await get_redis()
    key = f"history:{user_id}:{request_id}"

    if await r.exists(key):
        await r.delete(key)
        # Remove from list
        await r.lrem(f"user:{user_id}:history", 0, request_id)
        return True

    return False
