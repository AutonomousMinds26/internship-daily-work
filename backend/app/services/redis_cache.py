import json
import redis
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Resilient connection initialization
redis_client = None
try:
    redis_client = redis.from_url(
        settings.REDIS_URL, 
        decode_responses=True, 
        socket_connect_timeout=2.0
    )
except Exception as e:
    logger.error(f"Failed to initialize Redis client: {str(e)}")

def get_cached_candidate(candidate_id: int) -> Optional[dict]:
    if not redis_client:
        return None
    try:
        cache_key = f"candidate:{candidate_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"CACHE HIT: Candidate {candidate_id} found in Redis.")
            return json.loads(cached_data)
        logger.info(f"CACHE MISS: Candidate {candidate_id} not found in Redis.")
        return None
    except Exception as e:
        logger.error(f"Redis get failed for candidate {candidate_id}: {str(e)}")
        return None

def cache_candidate(candidate_id: int, candidate_data: dict, ttl: int = 3600):
    if not redis_client:
        return
    try:
        cache_key = f"candidate:{candidate_id}"
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(candidate_data)
        )
        logger.info(f"CACHE WRITE: Candidate {candidate_id} cached in Redis with TTL={ttl}s.")
    except Exception as e:
        logger.error(f"Redis set failed for candidate {candidate_id}: {str(e)}")

def invalidate_candidate(candidate_id: int):
    if not redis_client:
        return
    try:
        cache_key = f"candidate:{candidate_id}"
        redis_client.delete(cache_key)
        logger.info(f"CACHE INVALIDATE: Candidate {candidate_id} removed from Redis.")
    except Exception as e:
        logger.error(f"Redis delete failed for candidate {candidate_id}: {str(e)}")
