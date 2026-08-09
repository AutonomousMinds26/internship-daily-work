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

# --- Job Caching ---
def get_cached_job(job_id: int) -> Optional[dict]:
    if not redis_client:
        return None
    try:
        cache_key = f"job:{job_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"CACHE HIT: Job {job_id} found in Redis.")
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Redis get failed for job {job_id}: {str(e)}")
        return None

def cache_job(job_id: int, job_data: dict, ttl: int = 3600):
    if not redis_client:
        return
    try:
        cache_key = f"job:{job_id}"
        redis_client.setex(cache_key, ttl, json.dumps(job_data))
        logger.info(f"CACHE WRITE: Job {job_id} cached in Redis.")
    except Exception as e:
        logger.error(f"Redis set failed for job {job_id}: {str(e)}")

def invalidate_job(job_id: int):
    if not redis_client:
        return
    try:
        cache_key = f"job:{job_id}"
        redis_client.delete(cache_key)
        logger.info(f"CACHE INVALIDATE: Job {job_id} removed from Redis.")
    except Exception as e:
        logger.error(f"Redis delete failed for job {job_id}: {str(e)}")

# --- Candidate Score Caching ---
def get_cached_score(candidate_id: int, job_id: int) -> Optional[dict]:
    if not redis_client:
        return None
    try:
        cache_key = f"score:{candidate_id}:{job_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"CACHE HIT: Score for candidate {candidate_id} and job {job_id} found in Redis.")
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Redis get failed for score {candidate_id}:{job_id}: {str(e)}")
        return None

def cache_score(candidate_id: int, job_id: int, score_data: dict, ttl: int = 3600):
    if not redis_client:
        return
    try:
        cache_key = f"score:{candidate_id}:{job_id}"
        redis_client.setex(cache_key, ttl, json.dumps(score_data))
        logger.info(f"CACHE WRITE: Score for candidate {candidate_id} and job {job_id} cached in Redis.")
    except Exception as e:
        logger.error(f"Redis set failed for score {candidate_id}:{job_id}: {str(e)}")

# --- LLM Response Caching ---
def get_cached_llm_response(prompt_key: str) -> Optional[dict]:
    if not redis_client:
        return None
    try:
        cache_key = f"llm:{prompt_key}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"CACHE HIT: LLM response for key '{prompt_key[:20]}...' found in Redis.")
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Redis get failed for LLM key {prompt_key}: {str(e)}")
        return None

def cache_llm_response(prompt_key: str, response_data: dict, ttl: int = 7200):
    if not redis_client:
        return
    try:
        cache_key = f"llm:{prompt_key}"
        redis_client.setex(cache_key, ttl, json.dumps(response_data))
        logger.info(f"CACHE WRITE: LLM response for key '{prompt_key[:20]}...' cached in Redis.")
    except Exception as e:
        logger.error(f"Redis set failed for LLM key {prompt_key}: {str(e)}")

